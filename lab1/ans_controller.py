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

# For an introduction with a dump L2 switch see: https://ryu.readthedocs.io/en/latest/writing_ryu_app.html
# For examples see: https://github.com/faucetsdn/ryu/tree/master/ryu/app
# For logging see: https://docs.python.org/3/library/logging.html

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3, ether
from ryu.utils import hex_array
from ryu.lib.packet import packet, ethernet, ether_types # for L2 packets
from ryu.lib.packet import ipv4, arp, icmp # for L3 and L4 packets
import ipaddress

class LearningSwitch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(LearningSwitch, self).__init__(*args, **kwargs)

        # Here you can initialize the data structures you want to keep at the controller
        
        self.router = 3 # The router is the switch with DPID 3

        # Layer 2 switch MAC address table
        self.mac_port_map = {} # {dp_id: {mac: port}}

        # Layer 3 router port MACs and IP addresses

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
    
    # Handle the packet_in event
    # See: https://ryu.readthedocs.io/en/latest/ofproto_v1_3_ref.html#packet-in-message
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        self.logger.info("Packet received from switch: (DPID %d)", datapath.id)
        
        if datapath.id == self.router: # check types
            self.logger.info("Router selected")
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
            # Handle IP packets here
            ip_pkt = pkt.get_protocol(ipv4.ipv4)
            src_ip = ip_pkt.src
            dst_ip = ip_pkt.dst
            # check if dstip is a router ip but only the gateway ip of the current host
            if self.router_port_to_own_ip[in_port] == dst_ip:
                # check if the packet is an ICMP echo request
                if ip_pkt.proto == ipv4.inet.IPPROTO_ICMP:
                    self.logger.info("Received ICMP echo request from %s to %s", src_ip, dst_ip)
                    self._handle_icmp_request(dp, ip_pkt, eth, in_port)
                else:
                    self.logger.info("unsupported protocol")
            else: # packet is not for the router (actual routing)
                self.logger.info("Packet is not for the router")
                # check to which subnet the dstip belongs to determine the out_port
                if self._in_same_subnet(dst_ip, self.router_port_to_own_ip[1]):
                    out_port = 1
                elif self._in_same_subnet(dst_ip, self.router_port_to_own_ip[2]):
                    out_port = 2
                elif self._in_same_subnet(dst_ip, self.router_port_to_own_ip[3]):
                    self.logger.info("Packet is for the external network")
                    # drop the packet, no communication with the external network allowed
                    return
                
                if self._in_same_subnet(src_ip, self.router_port_to_own_ip[3]):
                    self.logger.info("Packet is from the external network")
                    # drop the packet, no communication with the external network allowed
                    return
                
                if out_port == in_port: # same subnet
                    # drop the packet, no communication with the same port allowed
                    return
                
                # Check if the destination MAC address is known
                if dst_ip in self.router_arp_table:
                    self._route_packet(dp, in_port, out_port, dst_ip, pkt)
                else:
                    # Buffer the packet until the ARP reply is received
                    self.router_event_buffer.append((ev, dst_ip))
                    # Send an ARP request to learn the MAC address of the destination IP
                    self._send_arp_request(dp, out_port, dst_ip)
                    return
        elif eth.ethertype == ether_types.ETH_TYPE_ARP:
            # Handle ARP packets here
            arp_pkt = pkt.get_protocol(arp.arp)
            if arp_pkt.opcode == arp.ARP_REQUEST:
                self._handle_arp_request(dp, arp_pkt, eth, in_port)
            elif arp_pkt.opcode == arp.ARP_REPLY:
                self._handle_arp_reply(dp, arp_pkt, eth, in_port)
        elif eth.ethertype == ether_types.ETH_TYPE_IPV6:
            pass # disable IPv6 logging
        else:
            self.logger.info("Unsupported ethertype: %s", hex(eth.ethertype))
        return
    
    def _route_packet(self, dp, in_port, out_port, dst_ip, pkt):
        # Route the packet to the destination port
        ofp_parser = dp.ofproto_parser
        ofp = dp.ofproto
        
        dst_mac = self.router_arp_table[dst_ip]
        src_mac = self.router_port_to_own_mac[in_port]
        
        match = ofp_parser.OFPMatch(in_port=in_port, ipv4_dst=dst_ip)
        
        # Manipulate the ethernet header
        # see: https://ryu.readthedocs.io/en/latest/ofproto_v1_3_ref.html#ryu.ofproto.ofproto_v1_3_parser.OFPActionSetField
        actions = [
            ofp_parser.OFPActionOutput(out_port),
            ofp_parser.OFPActionSetField(eth_src=src_mac),
            ofp_parser.OFPActionSetField(eth_dst=dst_mac)
        ]
        
        self.add_flow(dp, 1, match, actions) # Add a flow to the router
        
        msg = ofp_parser.OFPPacketOut(dp, ofp.OFP_NO_BUFFER, in_port, actions, pkt.data)
        dp.send_msg(msg)
    
    def _send_arp_request(self, dp, out_port, dst_ip):
        ofp_parser = dp.ofproto_parser
        ofp = dp.ofproto
        
        router_mac = self.router_port_to_own_mac[out_port]
        src_ip = self.router_port_to_own_ip[out_port]
        
        # Create an ARP request packet
        arp_request = arp.arp(
            opcode=arp.ARP_REQUEST,
            src_mac=router_mac,
            src_ip=src_ip,
            dst_ip=dst_ip)
        eth_request = ethernet.ethernet(ethertype=ether_types.ETH_TYPE_ARP, dst='ff:ff:ff:ff:ff:ff', src=router_mac)
        
        out_pkt = packet.Packet()
        out_pkt.add_protocol(eth_request) # Create Ethernet header
        out_pkt.add_protocol(arp_request) # Add ARP request to the packet
        out_pkt.serialize()
        
        actions = [dp.ofproto_parser.OFPActionOutput(out_port)]
        
        msg = ofp_parser.OFPPacketOut(dp, ofp.OFP_NO_BUFFER, out_port, actions, out_pkt)
        dp.send_msg(msg)
    
    def _handle_icmp_request(self, dp, ip_pkt, eth, in_port):
        eth_reply = ethernet.ethernet(dst=eth.src, src=eth.dst, ethertype=ether.ETH_TYPE_IP)
        ip_reply = ipv4.ipv4(dst=ip_pkt.src, src=ip_pkt.dst, proto=ipv4.inet.IPPROTO_ICMP)
        
        # Create an ICMP reply packet
        # see: https://ryu.readthedocs.io/en/latest/library_packet_ref/packet_icmp.html
        icmp_reply = icmp.icmp( 
            type_=icmp.ICMP_ECHO_REPLY,
            code=0,
            csum=0,
            data=ip_pkt)
        
        reply_pkt = packet.Packet()
        reply_pkt.add_protocol(eth_reply)
        reply_pkt.add_protocol(ip_reply)
        reply_pkt.add_protocol(icmp_reply)
        reply_pkt.serialize()
        
        actions = [dp.ofproto_parser.OFPActionOutput(in_port)]
        
        ofp_parser = dp.ofproto_parser
        ofp = dp.ofproto
        
        # Send the ICMP reply back to the host
        out = ofp_parser.OFPPacketOut(
            datapath=dp,
            buffer_id=ofp.OFP_NO_BUFFER,
            in_port=ofp.OFPP_CONTROLLER,
            actions=actions,
            data=reply_pkt.data
        )
        dp.send_msg(out)
    
    # @todo: clean comments (remove llm comments)
    def _handle_arp_request(self, dp, arp_pkt, eth, in_port):
        # Check if the request is for one of the router's IP addresses
        if arp_pkt.dst_ip in self.router_port_to_own_ip.values():
            # Send an ARP reply
            self.logger.info("Received ARP Request: who-has %s? Tell %s",
                            arp_pkt.dst_ip, arp_pkt.src_ip)
            # Get the port number of the incoming interface
            out_port = in_port
            # Get the MAC address of the router's interface
            router_mac = self.router_port_to_own_mac[out_port]
            # Create an ARP reply packet
            arp_reply = arp.arp(
                opcode=arp.ARP_REPLY,
                src_mac=router_mac,
                src_ip=arp_pkt.dst_ip,
                dst_mac=arp_pkt.src_mac,
                dst_ip=arp_pkt.src_ip)
            # Send the ARP reply back to the host
            eth_reply = ethernet.ethernet(ethertype=ether_types.ETH_TYPE_ARP, dst=eth.src, src=router_mac)
            actions = [dp.ofproto_parser.OFPActionOutput(in_port)]
            out_pkt = packet.Packet()
            out_pkt.add_protocol(eth_reply) # Create Ethernet header
            out_pkt.add_protocol(arp_reply) # Add ARP reply to the packet
            out_pkt.serialize()
            ofp_parser = dp.ofproto_parser
            ofp = dp.ofproto
            msg = ofp_parser.OFPPacketOut(dp, ofp.OFP_NO_BUFFER, in_port, actions, out_pkt)
            dp.send_msg(msg) # 	Queue an OpenFlow message to send to the corresponding switch
        else:
            # drop the packet, not for the router
            pass
        # Update own ARP table
        self.router_arp_table[arp_pkt.src_ip] = arp_pkt.src_mac
        self.logger.info("Updated ARP table: %s -> %s", arp_pkt.src_ip, arp_pkt.src_mac)
        
    def _handle_arp_reply(self, dp, arp_pkt, eth, in_port):
        # check if the reply is for one of the router's IP addresses
        if arp_pkt.dst_ip in self.router_port_to_own_ip.values():
            # Update the ARP table
            self.router_arp_table[arp_pkt.src_ip] = arp_pkt.src_mac
            self.logger.info("Updated ARP table: %s -> %s", arp_pkt.src_ip, arp_pkt.src_mac)
            # Continue with previously buffered packets (e.g. ICMP echo requests)
            for (ev, dst_ip) in self.router_event_buffer:
                if dst_ip in self.router_arp_table:
                    self._packet_in_router_handler(ev)
                    self.router_event_buffer.remove((ev, dst_ip))
        else: 
            # drop the packet, not for the router
            pass

    def _packet_in_switch_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath               # See: https://ryu.readthedocs.io/en/latest/ryu_app_api.html#ryu-controller-controller-datapath
        dp_id = dp.id                   # 64-bit OpenFlow Datapath ID to identify the switch
        ofp = dp.ofproto                # OpenFlow definitions
        ofp_parser = dp.ofproto_parser  # OpenFlow wire message encoder and decoder

        # Your controller implementation should start here
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
        msg = ofp_parser.OFPPacketOut(dp, ofp.OFP_NO_BUFFER, in_port, actions, msg.data)
        dp.send_msg(msg) # 	Queue an OpenFlow message to send to the corresponding switch
        
    def _in_same_subnet(ip1, ip2):
        network1 = ipaddress.ip_network(f"{ip1}/24", strict=False) # 255.255.255.0 -> 11111111.11111111.11111111.00000000 -> /24
        network2 = ipaddress.ip_network(f"{ip2}/24", strict=False)
        return network1.network_address == network2.network_address
