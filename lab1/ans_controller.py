"""
 Copyright (c) 2025 Computer Networks Group @ UPB

 Permission is hereby granted, free of charge, to any person obtaining a copy of
 this software and associated documentation files (the "Software"), to deal in
 the Software without restriction, including without limitation the rights to
 use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
 the Software, and to permit persons to whom the Software is furnished to do so,
 subject to the following conditions:

 The above copyright notice and this permission notice shall be included in all
 copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
 FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
 COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
 IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 """

# For an Ryu introduction with a dump L2 switch see: https://ryu.readthedocs.io/en/latest/writing_ryu_app.html
# For Ryu examples see: https://github.com/faucetsdn/ryu/tree/master/ryu/app
# For Mininet API see: https://mininet.org/api/hierarchy.html
# For Mininet getting started see: https://github.com/mininet/mininet/wiki/Introduction-to-Mininet
# For logging see: https://docs.python.org/3/library/logging.html

# Start the controller with: ryu-manager ans_controller.py

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3, ether
from ryu.utils import hex_array
from ryu.lib.packet import packet, ethernet, ether_types, ipv4, arp, icmp
import ipaddress

class LearningSwitch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(LearningSwitch, self).__init__(*args, **kwargs)
        
        # Layer 2 switch MAC address table
        self.mac_port_map = {} # {dp_id: {mac: port}}

        # Layer 3 router port MACs and IP addresses
        self.router = 3 # The router is the switch with DPID 3

        # Router port MACs assumed by the controller
        self.router_port_to_own_mac = {
            1: "00:00:00:00:01:01",
            2: "00:00:00:00:01:02",
            3: "00:00:00:00:01:03"
        }
        # Router port (gateways) IP addresses assumed by the controller
        self.router_port_to_own_ip = {
            1: "10.0.1.1",
            2: "10.0.2.1",
            3: "192.168.1.1"
        }
        
        self.router_arp_table = {} # {h1_ip: h1_mac}
        
        # When the router needs to first learn the MAC address of a host,
        # it will buffer the packet (the event) until the ARP reply is received
        self.router_event_buffer = [] # [(event, dst_ip)]

    
    # Handle the packet_in event
    # See: https://ryu.readthedocs.io/en/latest/ofproto_v1_3_ref.html#packet-in-message
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        
        if datapath.id == self.router: # check types
            self._packet_in_router_handler(ev)
        else:
            self._packet_in_switch_handler(ev)
        return
    
    def _packet_in_router_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        
        if eth.ethertype == ether_types.ETH_TYPE_IP:
            ip_pkt = pkt.get_protocol(ipv4.ipv4)
            src_ip = ip_pkt.src
            dst_ip = ip_pkt.dst
            
            # check if dstip is a router ip but only the gateway ip of the current host
            if self.router_port_to_own_ip[in_port] == dst_ip:
                # check if the packet is an ICMP echo request
                if ip_pkt.proto == ipv4.inet.IPPROTO_ICMP:
                    self._handle_icmp_request(dp, pkt, in_port)
                else:
                    self.logger.info("unsupported protocol")
            else: # packet is not for the router (actual routing)
                self.logger.info("IP packet is not for the router, routing required")

                # check to which subnet the dstip belongs to determine the out_port
                if self._in_same_subnet(dst_ip, self.router_port_to_own_ip.get(1)):
                    out_port = 1
                elif self._in_same_subnet(dst_ip, self.router_port_to_own_ip.get(2)):
                    out_port = 2
                elif self._in_same_subnet(dst_ip, self.router_port_to_own_ip.get(3)):
                    self.logger.info("IP packet is for the external network, not allowed")
                    # drop the packet, no communication with the external network allowed
                    # could add a flow to the router to drop the packet
                    return
                else:
                    self.logger.info("Target subnet unknown")
                    # drop the packet
                    return
                
                if self._in_same_subnet(src_ip, self.router_port_to_own_ip[3]):
                    self.logger.info("IP packet is from the external network, not allowed")
                    # drop the packet, no communication with the external network allowed
                    # could add a flow to the router to drop the packet
                    return
                
                if out_port == in_port: # same subnet
                    self.logger.info("IP packet from %s (port %d) to %s (port %d) \
                                     is for same subnet but not for router",
                                     src_ip, in_port, dst_ip, out_port)
                    # drop the packet
                    return
                
                # Check if the destination MAC address is known
                if dst_ip in self.router_arp_table:
                    self.logger.info("Destination IP %s in ARP table, continue routing", dst_ip)
                    self._route_packet(dp, in_port, src_ip, out_port, dst_ip, pkt)
                    return
                else:
                    self.logger.info("Destination IP %s not in ARP table, send ARP request first", dst_ip)
                    # Buffer the packet until the ARP reply is received
                    self.router_event_buffer.append((ev, dst_ip))
                    # Send an ARP request to learn the MAC address of the destination IP
                    self._send_arp_request(dp, out_port, dst_ip)
                    return
                
        elif eth.ethertype == ether_types.ETH_TYPE_ARP:
            arp_pkt = pkt.get_protocol(arp.arp)
            
            if arp_pkt.opcode == arp.ARP_REQUEST:
                # Check if the request is for one of the router's IP addresses
                if arp_pkt.dst_ip in self.router_port_to_own_ip.values():
                    self._handle_arp_request(dp, arp_pkt, eth, in_port)
                else:
                    # drop the packet, not for the router
                    pass
                # Update own ARP table whenever a new MAC address is learned
                self.router_arp_table[arp_pkt.src_ip] = arp_pkt.src_mac
                self.logger.info("Updated ARP table: %s -> %s", arp_pkt.src_ip, arp_pkt.src_mac)
                
            elif arp_pkt.opcode == arp.ARP_REPLY:
                # check if the reply was sent to the router
                if arp_pkt.dst_ip in self.router_port_to_own_ip.values():
                    self._handle_arp_reply(arp_pkt)
                else:
                    # drop the packet, not for the router
                    return
                
        else:
            self.logger.debug("Unsupported ethertype: %s", hex(eth.ethertype))
    
    def _route_packet(self, dp, in_port, src_ip, out_port, dst_ip, pkt):
        # Route the packet to the destination port
        ofp_parser = dp.ofproto_parser
        ofp = dp.ofproto
        
        dst_mac = self.router_arp_table[dst_ip]
        src_mac = self.router_port_to_own_mac[in_port]
        
        self.logger.info("Routing packet from %s (port %d) to %s port(%d)", src_ip, in_port, dst_ip, out_port)
        
        # Create a match rule for the flow
        # see: https://ryu.readthedocs.io/en/latest/ofproto_v1_3_ref.html#flow-match-structure
        match = ofp_parser.OFPMatch(
            in_port=in_port,
            eth_type=ether_types.ETH_TYPE_IP,
            ipv4_dst=dst_ip) # add ipv4_src if flow should be host specific
        
        # Manipulate the ethernet header
        # see: https://ryu.readthedocs.io/en/latest/ofproto_v1_3_ref.html#ryu.ofproto.ofproto_v1_3_parser.OFPActionSetField
        actions = [
            ofp_parser.OFPActionSetField(eth_src=src_mac), # the order of the actions is important
            ofp_parser.OFPActionSetField(eth_dst=dst_mac),
            ofp_parser.OFPActionOutput(out_port)
        ]
        
        self.add_flow(dp, 1, match, actions) # Add a flow to the router
        self.logger.info("Flow added to router: ETH_TYPE_IP @ in_port %d -> %s: Change MACs and output at out_port %d", in_port, dst_ip, out_port)
        
        msg = ofp_parser.OFPPacketOut(
            datapath=dp, 
            buffer_id=ofp.OFP_NO_BUFFER,
            in_port=in_port, # test: changed this to OFPP_CONTROLLER
            actions=actions,
            data=pkt.data)
        dp.send_msg(msg)
    
    def _send_arp_request(self, dp, out_port, dst_ip):
        ofp_parser = dp.ofproto_parser
        ofp = dp.ofproto
        
        router_mac = self.router_port_to_own_mac[out_port]
        src_ip = self.router_port_to_own_ip[out_port]
        
        self.logger.info("Sending ARP Request on port %d: Who-has %s? Tell %s", out_port, dst_ip, src_ip)
        
        # Create an Ethernet header for the ARP request
        # see: https://ryu.readthedocs.io/en/latest/library_packet_ref/packet_ethernet.html#ryu.lib.packet.ethernet.ethernet
        eth_request = ethernet.ethernet(
            ethertype=ether_types.ETH_TYPE_ARP,
            dst='ff:ff:ff:ff:ff:ff',
            src=router_mac)
        
        # Create an ARP request packet
        # see: https://ryu.readthedocs.io/en/latest/library_packet_ref/packet_arp.html#ryu.lib.packet.arp.arp
        arp_request = arp.arp(
            opcode=arp.ARP_REQUEST,
            src_mac=router_mac,
            dst_mac='ff:ff:ff:ff:ff:ff',
            src_ip=src_ip,
            dst_ip=dst_ip)
        
        out_pkt = packet.Packet()
        out_pkt.add_protocol(eth_request) # Create Ethernet header
        out_pkt.add_protocol(arp_request) # Add ARP request to the packet
        out_pkt.serialize()
        
        actions = [dp.ofproto_parser.OFPActionOutput(out_port)]
        
        msg = ofp_parser.OFPPacketOut(
            datapath=dp,
            buffer_id=ofp.OFP_NO_BUFFER,
            in_port=ofp.OFPP_CONTROLLER, # important: not in_port but OFPP_CONTROLLER
            actions=actions,
            data=out_pkt)
        
        dp.send_msg(msg)
    
    def _handle_icmp_request(self, dp, pkt, in_port):
        ofp_parser = dp.ofproto_parser
        ofp = dp.ofproto
        
        eth = pkt.get_protocol(ethernet.ethernet)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        icmp_pkt = pkt.get_protocol(icmp.icmp)
        echo_req = icmp_pkt.data

        self.logger.info("Received ICMP echo request from %s to %s", ip_pkt.src, ip_pkt.dst)
        self.logger.info("Sending ICMP echo reply to %s on port %d", ip_pkt.src, in_port)

        # Create an Ethernet header for the ICMP reply
        eth_reply = ethernet.ethernet(
            dst=eth.src,
            src=eth.dst,
            ethertype=ether.ETH_TYPE_IP)
        
        # Create an IP header for the ICMP reply
        # see: https://ryu.readthedocs.io/en/latest/library_packet_ref/packet_ipv4.html#ryu.lib.packet.ipv4.ipv4
        ip_reply = ipv4.ipv4(
            dst=ip_pkt.src,
            src=ip_pkt.dst,
            proto=ipv4.inet.IPPROTO_ICMP)
        
        # Create an ICMP reply packet
        # see: https://ryu.readthedocs.io/en/latest/library_packet_ref/packet_icmp.html
        icmp_reply = icmp.icmp( 
            type_=icmp.ICMP_ECHO_REPLY,
            code=0, # ICMP code for echo reply
            csum=0, # checksum will be calculated automatically
            data=icmp.echo(id_=echo_req.id, seq=echo_req.seq, data=echo_req.data))
        
        reply_pkt = packet.Packet()
        reply_pkt.add_protocol(eth_reply)
        reply_pkt.add_protocol(ip_reply)
        reply_pkt.add_protocol(icmp_reply)
        reply_pkt.serialize()
        
        actions = [dp.ofproto_parser.OFPActionOutput(in_port)]
        
        # Send the ICMP reply back to the host
        # Setting in_port = ofp.OFPP_CONTROLLER is important, packet is generated by the controller
        out = ofp_parser.OFPPacketOut(
            datapath=dp,
            buffer_id=ofp.OFP_NO_BUFFER,
            in_port=ofp.OFPP_CONTROLLER,
            actions=actions,
            data=reply_pkt.data)
        
        dp.send_msg(out)
    
    def _handle_arp_request(self, dp, arp_pkt, eth, in_port):
        ofp_parser = dp.ofproto_parser
        ofp = dp.ofproto
        
        self.logger.info("Received ARP Request: Who-has %s? Tell %s", arp_pkt.dst_ip, arp_pkt.src_ip)
        
        out_port = in_port
        router_mac = self.router_port_to_own_mac[out_port]
        
        # Create an Ethernet header for the ARP reply
        eth_reply = ethernet.ethernet(
            ethertype=ether_types.ETH_TYPE_ARP,
            dst=eth.src,
            src=router_mac)
        
        # Create an ARP reply packet
        # see: https://ryu.readthedocs.io/en/latest/library_packet_ref/packet_arp.html#ryu.lib.packet.arp.arp
        arp_reply = arp.arp(
            opcode=arp.ARP_REPLY,
            src_mac=router_mac,
            src_ip=arp_pkt.dst_ip,
            dst_mac=arp_pkt.src_mac,
            dst_ip=arp_pkt.src_ip)
        
        out_pkt = packet.Packet()
        out_pkt.add_protocol(eth_reply) # Create Ethernet header
        out_pkt.add_protocol(arp_reply) # Add ARP reply to the packet
        out_pkt.serialize()
        
        actions = [dp.ofproto_parser.OFPActionOutput(in_port)]
        
        # Setting in_port = ofp.OFPP_CONTROLLER is important, packet is generated by the controller
        msg = ofp_parser.OFPPacketOut(
            datapath=dp,
            buffer_id=ofp.OFP_NO_BUFFER,
            in_port=ofp.OFPP_CONTROLLER,
            actions=actions,
            data=out_pkt)
        
        dp.send_msg(msg)
        
        self.logger.info("Sent ARP Reply: %s is at %s", arp_pkt.dst_ip, router_mac)
        
    def _handle_arp_reply(self, arp_pkt):
        # Update the ARP table
        self.router_arp_table[arp_pkt.src_ip] = arp_pkt.src_mac
        self.logger.info("Updated ARP table: %s -> %s", arp_pkt.src_ip, arp_pkt.src_mac)
        
        # Continue with previously buffered packets (e.g. ICMP echo requests)
        for (ev, dst_ip) in self.router_event_buffer:
            if dst_ip in self.router_arp_table:
                self.logger.info("Continuing with buffered packet for %s", dst_ip)
                self._packet_in_router_handler(ev)
                self.router_event_buffer.remove((ev, dst_ip))

    def _packet_in_switch_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath               # See: https://ryu.readthedocs.io/en/latest/ryu_app_api.html#ryu-controller-controller-datapath
        dp_id = dp.id                   # 64-bit OpenFlow Datapath ID to identify the switch
        ofp = dp.ofproto                # OpenFlow definitions
        ofp_parser = dp.ofproto_parser  # OpenFlow wire message encoder and decoder

        in_port = msg.match['in_port']

        if msg.reason == ofp.OFPR_NO_MATCH:
            reason = 'NO MATCH'
        else:
            reason = 'not supported yet'

        self.logger.debug('OFPPacketIn received on port %d: '
                            'buffer_id=%x total_len=%d reason=%s '
                            'table_id=%d cookie=%d match=%s data=%s',
                            in_port, msg.buffer_id, msg.total_len, reason,
                            msg.table_id, msg.cookie, msg.match,
                            hex_array(msg.data))
        
        # Parse the packet
        # See: https://ryu.readthedocs.io/en/latest/library_packet.html
        # See: https://ryu.readthedocs.io/en/latest/library_packet_ref/packet_ethernet.html#module-ryu.lib.packet.ethernet
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        
        eth_src = eth.src
        eth_dst = eth.dst

        # Learn the MAC address and port mapping (step 1)
        if dp_id not in self.mac_port_map:
            self.mac_port_map[dp_id] = {} # Initialize the mapping for this new switch
        self.mac_port_map[dp_id][eth_src] = in_port # Memorize the source MAC on the current port
        # Do not install a flow here, pre-installing flows for hypothetical future packets could create stale routes
        # Only install paths as they are needed, see below.

        # Check if the destination MAC address is known (step 2)
        # Only install the flow when a packet is sent to a known MAC address to verify the path exists, ensuring the flow is only installed when needed.
        if eth_dst in self.mac_port_map[dp_id]:
            out_port = self.mac_port_map[dp_id][eth_dst] # Forward the packet to the corresponding port
            match = ofp_parser.OFPMatch(in_port=in_port, eth_dst=eth_dst) # New match rule
            actions = [ofp_parser.OFPActionOutput(out_port)]
            self.add_flow(dp, 1, match, actions) # Add a flow to the switch
        else:
            out_port = ofp.OFPP_FLOOD # Flood on all ports
            actions = [ofp_parser.OFPActionOutput(out_port)]
            # This also covers the broadcast case, where the destination MAC is a broadcast address (ff:ff:ff:ff:ff:ff)
            # because the switch will never learn an entry for the broadcast address.

        # Send the packet out to the switch either to the known port or flood it
        # See: https://ryu.readthedocs.io/en/latest/ofproto_v1_3_ref.html#ryu.ofproto.ofproto_v1_3_parser.OFPPacketOut
        msg = ofp_parser.OFPPacketOut(
            datapath=dp,
            buffer_id=ofp.OFP_NO_BUFFER,
            in_port=in_port,
            actions=actions,
            data=msg.data)
        
        dp.send_msg(msg) # 	Queue an OpenFlow message to send to the corresponding switch
        
    def _in_same_subnet(self, ip1, ip2, netmask='255.255.255.0'):
        net = ipaddress.IPv4Network(f"0.0.0.0/{netmask}")
        prefix_len = net.prefixlen
        network1 = ipaddress.ip_network(f"{ip1}/{prefix_len}", strict=False)
        network2 = ipaddress.ip_network(f"{ip2}/{prefix_len}", strict=False)
        return network1.network_address == network2.network_address

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Initial flow entry for matching misses
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    # Add a flow entry to the flow-table
    # See: https://ryu.readthedocs.io/en/latest/ofproto_v1_3_ref.html#ryu.ofproto.ofproto_v1_3_parser.OFPFlowMod
    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Construct flow_mod message and send it
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)
