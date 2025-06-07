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

#!/usr/bin/env python3

import copy
import ipaddress
from ryu.base import app_manager
from ryu.controller import mac_to_port
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link
from ryu.app.wsgi import ControllerBase

import topo

class SPRouter(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SPRouter, self).__init__(*args, **kwargs)
        
        # Initialize the topology with #ports=4
        self.k = 4
        self.topo_net = topo.Fattree(self.k)
        
        self.arp_table = {} # {ip: mac}

        self.dpid_to_ip = {} # {dpid: ip
        self.ip_to_dpid = {} # {ip: dpid}
        for switch in self.topo_net.switches:
            dpid = self._ip_to_dpid(switch.ip) # use the same encoding as in the Mininet topology
            self.ip_to_dpid[switch.ip] = dpid
            self.dpid_to_ip[dpid] = switch.ip

        self.dpid_to_port = {} # {dpid_src: {dpid_dst: src_port}}
        self.host_ip_to_port = {} # {ip: port}

        # Each router has a list of events that it has received but not yet processed
        self.event_buffer = {} # {dpid: [(event, dst_ip)]}
    
    def _ip_to_dpid(self, ip):
        # Convert IP to integer
        ip_int = int(ipaddress.IPv4Address(ip))
        return ip_int

    # Topology discovery
    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):
        # Switches and links in the network
        # The Function get_switch(self, None) outputs the list of switches.
        self.topo_raw_switches = copy.copy(get_switch(self, None))
        # The Function get_link(self, None) outputs the list of links.
        self.topo_raw_links = copy.copy(get_link(self, None))

        # self.logger.info(" \t" + "Current Links:")
        for l in self.topo_raw_links:
            if l.src.dpid not in self.dpid_to_port:
                self.dpid_to_port[l.src.dpid] = {}
            if l.dst.dpid not in self.dpid_to_port:
                self.dpid_to_port[l.dst.dpid] = {}
            # Store the source and destination ports for each link
            self.dpid_to_port[l.src.dpid][l.dst.dpid] = l.src.port_no # {dpid_src: {dpid_dst: src_port}}
            self.dpid_to_port[l.dst.dpid][l.src.dpid] = l.dst.port_no # {dpid_dst: {dpid_src: dst_port}}
            # print(" \t\t" + str(l))

        # self.logger.info(" \t" + "Current Switches:")
        for s in self.topo_raw_switches:
            # print(" \t\t" + str(s))
            pass

        if len(self.topo_raw_switches) == len(self.topo_net.switches):
            self.logger.info("Topology discovery successful: %d switches found", len(self.topo_raw_switches))
            self.add_ft_routing_flows()

    def add_ft_routing_flows(self):
        k = self.k
        parser = # TODO: get parser without having a dp object

        # Algorithm 1: Generating aggregation switch routing tables
        for pod_x in range(0, k-1 + 1):
            for switch_z in range(k//2, k-1 + 1):
                switch_ip = f"10.{pod_x}.{switch_z}.1"
                switch_dpid = self.ip_to_dpid[switch_ip]
                for subnet_i in range(0, (k//2)-1 + 1):
                    # addPrefix(switch=10.pod_x.switch_z.1, prefix=10.pod_x.subnet_i.0/24, port=i) # high priority
                    # ft_port i -> ip address -> dpid -> topo_port
                    out_ip = f"10.{pod_x}.{subnet_i}.1"
                    out_dpid = self.ip_to_dpid[out_ip]
                    out_port = self.dpid_to_port[switch_dpid][out_dpid]

                    # Create a match rule for the flow
                    match = parser.OFPMatch(
                        in_port=in_port,
                        eth_type=ether_types.ETH_TYPE_IP,
                        ipv4_dst=dst_ip)
                    
                    # Manipulate the ethernet header
                    actions = [
                        parser.OFPActionSetField(eth_dst=dst_mac),
                        parser.OFPActionSetField(eth_src=src_mac),
                        parser.OFPActionOutput(out_port)
                    ]

                    self.add_flow(dp, 1, match, actions)

                # addPrefix(switch=10.pod_x.switch_z.1, suffix=0.0.0.0/0, )
                for host_i in range(2, (k//2)+1 + 1):
                    # addSuffix(switch=10.pod_x.switch_z.1, suffix=0.0.0.host_i/8, port=((host_i - 2 + z) mod (k//2) + k//2)) # low priority
                    ft_port = (host_i - 2 + switch_z) % (k//2) + k//2
                    # (src{2, 3}, dst{2, 3}) ->  1.1, 1.2, 2.1, 2.2
                    out_ip = f"10.{k}.{(switch_z//2)+1}.{(ft_port//2)+1}"
                    out_dpid = self.ip_to_dpid[out_ip]
                    out_port = self.dpid_to_port[switch_dpid][out_dpid]
                    pass

        # TODO: edge layer switch flows

        # Algorithm 2: Generating core switch routing table
            
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Install entry-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
    # Add a flow entry to the flow-table
    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Construct flow_mod message and send it
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        dpid = dp.id
        ofproto = dp.ofproto
        parser = dp.ofproto_parser
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        # TODO: handle new packets at the controller (ARP and IPv4 packets)
        
        if eth.ethertype == ether_types.ETH_TYPE_ARP:
            arp_pkt = pkt.get_protocol(arp.arp)

            self.host_ip_to_port[arp_pkt.src_ip] = in_port
            
            if arp_pkt.opcode == arp.ARP_REQUEST:
                # If the request is for one of the switch's IP addresses
                if arp_pkt.dst_ip == self.dpid_to_ip.get(dpid):
                    self._handle_arp_request(dp, arp_pkt, eth, in_port)
                else:
                    # Flood the packet, not for the switch
                    self.logger.info("ARP request for %s not handled by switch %s, flooding request", arp_pkt.dst_ip, self.dpid_to_ip[dpid])
                    out_ports = [i for i in range(1, self.k+1)]
                    for port in self.dpid_to_port[dpid].values():
                        out_ports.remove(port)
                    if in_port in out_ports:
                        out_ports.remove(in_port)
                    actions = [parser.OFPActionOutput(port) for port in out_ports]
                    # Send the packet out to the switch either to the known port or flood it
                    # See: https://ryu.readthedocs.io/en/latest/ofproto_v1_3_ref.html#ryu.ofproto.ofproto_v1_3_parser.OFPPacketOut
                    msg = parser.OFPPacketOut(
                        datapath=dp,
                        buffer_id=ofproto.OFP_NO_BUFFER,
                        in_port=in_port,
                        actions=actions,
                        data=msg.data)
                    
                    dp.send_msg(msg)

                # Update own ARP table whenever a new MAC address is learned
                self.arp_table[arp_pkt.src_ip] = arp_pkt.src_mac
                #self.logger.info("[Request] Updated ARP table: %s -> %s", arp_pkt.src_ip, arp_pkt.src_mac)
                
            elif arp_pkt.opcode == arp.ARP_REPLY:
                # Update the ARP table
                self.arp_table[arp_pkt.src_ip] = arp_pkt.src_mac
                #self.logger.info("[Reply] Updated ARP table: %s -> %s", arp_pkt.src_ip, arp_pkt.src_mac)

                # If the reply was sent to the switch
                if arp_pkt.dst_ip == self.dpid_to_ip.get(dpid):
                    self._handle_arp_reply(dpid, arp_pkt)
                else:
                    # Forward the ARP reply to the host
                    out_port = self.host_ip_to_port.get(arp_pkt.dst_ip)
                    actions = [parser.OFPActionOutput(out_port)]
                    # Send the packet out to the switch either to the known port or flood it
                    # See: https://ryu.readthedocs.io/en/latest/ofproto_v1_3_ref.html#ryu.ofproto.ofproto_v1_3_parser.OFPPacketOut
                    msg = parser.OFPPacketOut(
                        datapath=dp,
                        buffer_id=ofproto.OFP_NO_BUFFER,
                        in_port=in_port,
                        actions=actions,
                        data=msg.data)
                    
                    dp.send_msg(msg)
                
        elif eth.ethertype == ether_types.ETH_TYPE_IP:
            ip_pkt = pkt.get_protocol(ipv4.ipv4)
            src_ip = ip_pkt.src
            dst_ip = ip_pkt.dst

            #self.logger.info("Received IPv4 packet: src=%s, dst=%s", src_ip, dst_ip)
            
            # If the packet is destined for the current switch
            if dst_ip == self.dpid_to_ip.get(dpid):
                # Discard the packet, ICMP is not implemented
                self.logger.info("Packet destined for switch %s, but ICMP is not implemented. Discarding packet.", dpid)
            elif self._in_same_subnet(dst_ip, self.dpid_to_ip.get(dpid)):
                # Edge switch reached, forward the packet to the host directly
                if dst_ip in self.arp_table:
                    # If the target IP is in the ARP table, forward the packet to the host directly
                    dst_mac = self.arp_table[dst_ip]
                    src_mac = self.dpid_to_mac(dpid)
                    out_port = self.host_ip_to_port.get(dst_ip)
                    #self.logger.info("Forwarding packet to host %s with MAC %s on port %d", dst_ip, dst_mac, out_port)

                    # Create a match rule for the flow
                    match = parser.OFPMatch(
                        in_port=in_port,
                        eth_type=ether_types.ETH_TYPE_IP,
                        ipv4_dst=dst_ip)
                    
                    # Manipulate the ethernet header
                    actions = [
                        parser.OFPActionSetField(eth_dst=dst_mac),
                        parser.OFPActionSetField(eth_src=src_mac),
                        parser.OFPActionOutput(out_port)
                    ]

                    self.add_flow(dp, 1, match, actions)

                    # Forward the packet to the host
                    msg = parser.OFPPacketOut(
                        datapath=dp, 
                        buffer_id=ofproto_v1_3.OFP_NO_BUFFER,
                        in_port=in_port,
                        actions=actions,
                        data=pkt.data)
                    dp.send_msg(msg)
                else:
                    # If the target IP is not in the ARP table, buffer the event for later processing
                    #self.logger.info("Target IP %s not in ARP table, buffering event for later processing", dst_ip)
                    if dpid not in self.event_buffer:
                        self.event_buffer[dpid] = []
                    self.event_buffer[dpid].append((ev, dst_ip))
                    self._flood_arp_request(dp, dst_ip)
            else:
                # Else, the packet is not destined for the current switch, so FT routing is required
                # New switch, create prefix match rules and suffix match rules


                # Create a match rule for the flow
                # see: https://ryu.readthedocs.io/en/latest/ofproto_v1_3_ref.html#flow-match-structure
                match = parser.OFPMatch(
                    in_port=in_port,
                    eth_type=ether_types.ETH_TYPE_IP,
                    ipv4_dst=dst_ip)
                
                # Manipulate the ethernet header
                # see: https://ryu.readthedocs.io/en/latest/ofproto_v1_3_ref.html#ryu.ofproto.ofproto_v1_3_parser.OFPActionSetField
                actions = [
                    parser.OFPActionOutput(out_port)
                ]

                self.add_flow(dp, 1, match, actions) # Add a flow to the router

                # Forward the packet to the next hop
                msg = parser.OFPPacketOut(
                    datapath=dp, 
                    buffer_id=ofproto.OFP_NO_BUFFER,
                    in_port=in_port,
                    actions=actions,
                    data=pkt.data)
                dp.send_msg(msg)
        else:
            self.logger.debug("Unsupported ethertype: %s", hex(eth.ethertype))
    
    # Code from Lab1        
    def _handle_arp_request(self, dp, arp_pkt, eth, in_port):
        ofp_parser = dp.ofproto_parser
        ofp = dp.ofproto
                
        router_mac = self.dpid_to_mac(dp.id)  # Generate the router's MAC address based on its DPID
        
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
    
    # Code from Lab1
    def _handle_arp_reply(self, dpid, arp_pkt):
        # Update the ARP table
        self.arp_table[arp_pkt.src_ip] = arp_pkt.src_mac
        #self.logger.info("[Reply] Updated ARP table: %s -> %s", arp_pkt.src_ip, arp_pkt.src_mac)
        
        # Continue with previously buffered packets (e.g. ICMP echo requests)
        for (ev, dst_ip) in self.event_buffer.get(dpid, []):
            if dst_ip in self.arp_table:
                self.logger.info("Continuing with buffered packet for %s", dst_ip)
                self._packet_in_handler(ev)
                self.event_buffer[dpid].remove((ev, dst_ip))
    
    def _flood_arp_request(self, dp, dst_ip):
        ofp_parser = dp.ofproto_parser
        ofp = dp.ofproto
        
        router_mac = self.dpid_to_mac(dp.id)
        src_ip = self.dpid_to_ip.get(dp.id)
        
        self.logger.info("Flooding ARP Request: Who-has %s? Tell %s", dst_ip, src_ip)
        
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

        out_ports = [i for i in range(1, self.k+1)]
    
        for port in self.dpid_to_port[dp.id].values():
            out_ports.remove(port)

        actions = [dp.ofproto_parser.OFPActionOutput(port) for port in out_ports]
        
        msg = ofp_parser.OFPPacketOut(
            datapath=dp,
            buffer_id=ofp.OFP_NO_BUFFER,
            in_port=ofp.OFPP_CONTROLLER, # important: not in_port but OFPP_CONTROLLER
            actions=actions,
            data=out_pkt)
        
        dp.send_msg(msg)

    def _in_same_subnet(self, ip1, ip2, netmask='255.255.255.0'):
        net = ipaddress.IPv4Network(f"0.0.0.0/{netmask}")
        prefix_len = net.prefixlen
        network1 = ipaddress.ip_network(f"{ip1}/{prefix_len}", strict=False)
        network2 = ipaddress.ip_network(f"{ip2}/{prefix_len}", strict=False)
        return network1.network_address == network2.network_address
    
    def dpid_to_mac(self, dpid):
        mac = hex(int(dpid))[2:].zfill(12)  # Convert DPID to hex and pad with zeros
        mac = ':'.join(mac[i:i + 2] for i in range(0, len(mac), 2))  # Format as MAC address
        return mac