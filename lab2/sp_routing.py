
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
        self.topo_net = topo.Fattree(4)
        
        self.arp_table = {} # {ip: mac}
        self.dpid_to_ip = {} # {dpid: ip}

        # Each router has a list of events that it has received but not yet processed
        self.event_buffer = {} # {dpid: [(event, dst_ip)]}

    # Topology discovery
    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):
        # Switches and links in the network
        # The Function get_switch(self, None) outputs the list of switches.
        self.topo_raw_switches = copy.copy(get_switch(self, None))
        # The Function get_link(self, None) outputs the list of links.
        self.topo_raw_links = copy.copy(get_link(self, None))

        self.logger.info(" \t" + "Current Links:")
        for l in self.topo_raw_links:
            self.logger.info(" \t\t" + str(l))

        self.logger.info(" \t" + "Current Switches:")
        for s in self.topo_raw_switches:
            self.logger.info(" \t\t" + str(s))
            
        # TODO: Graph is already known (self.topo_net), but the ports must be added to the edges

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
        ''''
        If the packet is of type ARP
            If the packet is an ARP request
                If the packet is for the current router
                    Send ARP reply
            If the packet is an ARP reply to the router
                Update ARP table
                Continue with packets from event buffer of this router if possible
                
        If the packet is of type IPv4
            If the packet is destined for the current router
                Discard the packet, ICMP is not implemented
            If the packet is not destined for the current router (OSPF routing required)
                Derive the target router IP by masking the target IP, this is the target vertex for dijkstra's algorithm
                Execute Dijkstra's algorithm with the current router as the source vertex to find the shortest path to the target vertex by using the learned topology
                Determine the next hop in the path
                Get the MAC address of the next hop
                Create a match, actions entry and add it to the flow table
                Forward the packet to the next hop
        '''
        
        if eth.ethertype == ether_types.ETH_TYPE_ARP:
            arp_pkt = pkt.get_protocol(arp.arp)
            
            if arp_pkt.opcode == arp.ARP_REQUEST:
                # If the request is for one of the router's IP addresses
                if arp_pkt.dst_ip == self.dpid_to_ip.get(dpid):
                    self._handle_arp_request(dp, arp_pkt, eth, in_port)
                else:
                    # drop the packet, not for the router
                    pass
                # Update own ARP table whenever a new MAC address is learned
                self.arp_table[arp_pkt.src_ip] = arp_pkt.src_mac
                self.logger.info("Updated ARP table: %s -> %s", arp_pkt.src_ip, arp_pkt.src_mac)
                
            elif arp_pkt.opcode == arp.ARP_REPLY:
                # If the reply was sent to the router
                if arp_pkt.dst_ip == self.dpid_to_ip.get(dpid):
                    self._handle_arp_reply(dpid, arp_pkt)
                else:
                    # drop the packet, not for the router
                    return
                
        elif eth.ethertype == ether_types.ETH_TYPE_IP:
            ip_pkt = pkt.get_protocol(ipv4.ipv4)
            src_ip = ip_pkt.src
            dst_ip = ip_pkt.dst
            
            # If the packet is destined for the current router
            if dst_ip == self.dpid_to_ip.get(dpid):
                # Discard the packet, ICMP is not implemented
                pass
            else:
                # Derive the target router IP by masking the target IP
                # Execute Dijkstra's algorithm with the current router as the source vertex to find the shortest path to the target vertex by using the learned topology
                # Determine the next hop in the path
                # Get the MAC address of the next hop
                # Create a match, actions entry and add it to the flow table
                # Forward the packet to the next hop
                pass
        else:
            self.logger.debug("Unsupported ethertype: %s", hex(eth.ethertype))
    
    # Code from Lab1        
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
    
    # Code from Lab1
    def _handle_arp_reply(self, dpid, arp_pkt):
        # Update the ARP table
        self.arp_table[arp_pkt.src_ip] = arp_pkt.src_mac
        self.logger.info("Updated ARP table: %s -> %s", arp_pkt.src_ip, arp_pkt.src_mac)
        
        # Continue with previously buffered packets (e.g. ICMP echo requests)
        for (ev, dst_ip) in self.event_buffer.get(dpid, []):
            if dst_ip in self.arp_table:
                self.logger.info("Continuing with buffered packet for %s", dst_ip)
                self._packet_in_handler(ev)
                self.event_buffer[dpid].remove((ev, dst_ip))