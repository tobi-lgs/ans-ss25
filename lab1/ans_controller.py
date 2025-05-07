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
from ryu.ofproto import ofproto_v1_3
from ryu.utils import hex_array
from ryu.lib.packet import packet, ethernet, ether_types # for L2 packets
from ryu.lib.packet import ipv4, arp, icmp, tcp, udp # for L3 packets

class LearningSwitch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(LearningSwitch, self).__init__(*args, **kwargs)

        # Here you can initialize the data structures you want to keep at the controller

        # Layer 2 switch MAC address table
        self.mac_port_map = {} # {dp_id: {mac: port}}

        # Layer 3 router port MACs and IP addresses
        self.ip_port_map = {} # {dp_id : {ip: port}}
        self.ip_mac_map = {} # {dp_id : {ip: mac}}

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

        # For the router check the ethertype
        if eth.ethertype == ether_types.ETH_TYPE_IP:
            # Handle IP packets here
            ip = pkt.get_protocol(ipv4.ipv4)
            srcip = ip.src
            dstip = ip.dst
            protocol = ip.proto
            # Then check the protocol
            if protocol == protocol.IPPROTO_ICMP: # for ping
                pass # Handle ICMP packets here
            elif protocol == protocol.IPPROTO_TCP: # for iperf TCP
                pass # Handle TCP packets here
            elif protocol == protocol.IPPROTO_UDP: # for iperf UDP
                pass # Handle UDP packets here
            else:
                self.logger.info("Unsupported protocol: %s", protocol)
                return
        elif eth.ethertype == ether_types.ETH_TYPE_ARP:
            pass # Handle ARP packets here
        else:
            self.logger.info("Unsupported ethertype: %s", hex(eth.ethertype))
            return
        
        eth_src = eth.src
        eth_dst = eth.dst

        # Learn the MAC address and port mapping
        if dp_id not in self.mac_port_map:
            self.mac_port_map[dp_id] = {} # Initialize the mapping for this new switch
        self.mac_port_map[dp_id][eth_src] = in_port

        # Check if the destination MAC address is known
        if eth_dst in self.mac_port_map[dp_id]:
            out_port = self.mac_port_map[dp_id][eth_dst] # Forward the packet to the corresponding port
            match = ofp_parser.OFPMatch(in_port=in_port, eth_dst=eth_dst) # New match rule
            actions = [ofp_parser.OFPActionOutput(out_port)]
            self.add_flow(dp, 1, match, actions) # Add a flow to the switch
        else:
            out_port = ofp.OFPP_FLOOD # Flood on all ports
            actions = [ofp_parser.OFPActionOutput(out_port)]

        # Send the packet out to the switch either to the known port or flood it
        # See: https://ryu.readthedocs.io/en/latest/ofproto_v1_3_ref.html#ryu.ofproto.ofproto_v1_3_parser.OFPPacketOut
        msg = ofp_parser.OFPPacketOut(dp, ofp.OFP_NO_BUFFER, in_port, actions, msg.data)
        dp.send_msg(msg) # 	Queue an OpenFlow message to send to the corresponding switch