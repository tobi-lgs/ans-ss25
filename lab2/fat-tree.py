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

import ipaddress
import os
import subprocess
import time

import mininet
import mininet.clean
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import lg, info
from mininet.link import TCLink
from mininet.node import Node, OVSKernelSwitch, RemoteController
from mininet.topo import Topo
from mininet.util import waitListening, custom

from topo import Fattree
import topo

class FattreeNet(Topo):
    """
    Create a fat-tree network in Mininet
    """

    def __init__(self, ft_topo):

        Topo.__init__(self)
		# topology idea: [upperlayer_switches_pod1, lower_layer_switches_pod1, ...,upperlayer_switches_podk, lower_layer_switches_podk, core_switches] for number of switches in pod
        switches = ft_topo.switches
        servers = ft_topo.servers
        switch_host_dic = {} # {switch_id: switch_object}
        
        #for switch in switches:
        #    print(f"Adding switch {switch.id} with dpid {switch.id}")
        #for server in servers:
        #    print(f"Adding server {server.id} with dpid {server.id}")

        count = 0
        print("Start")
        for switch in switches:
            if switch.type == 'core_level_switch':
                switch_ip = switch.ip + "/24"
                dpid = ip_to_dpid(switch_ip)
                new_switch = self.addSwitch(f'switch{switch.id}', dpid=dpid)
                switch_host_dic[switch.id] = new_switch
                count+=1
                print(f"Adding core switch{switch.id} with IP {switch_ip}")
            else:
                # pod switches
                switch_ip = switch.ip + "/24"
                dpid = ip_to_dpid(switch_ip)
                new_switch = self.addSwitch(f'switch{switch.id}', dpid=dpid)
                switch_host_dic[switch.id] = new_switch
                count += 1
                print(f"Adding pod switch{switch.id} with IP {switch_ip}")
        print(f"Added {count} switches")

        count = 0
        for server in servers:
            id = server.id
            # Extracting the pod, switch, and host IDs from the server ID
            # A bit primitive, but works for the given format for the moment 
            # TODO: Make it a bit prettier :D --> Shit, the names from topo are allowed to be named after "pod_switch_host" with lower bindings...
            server_ip = server.ip + "/24" 
            server_network = ipaddress.ip_network(server_ip, strict=False)
            default_gateway = server_network.network_address + 1
            new_host = self.addHost(f'srv{server.id}', ip=server_ip, defaultRoute='via ' + str(default_gateway))
            switch_host_dic[server.id] = new_host
            count += 1
            print(f"Adding server {server.id} with IP {server_ip} and gateway {default_gateway}")
        print(f"Added {count} servers")

        nodes = []
        nodes.extend(switches)
        nodes.extend(servers) # optional: if all edges of switches are set, servers will be connected
        count = 0
            
        # Collect all edges to add without duplicates
        all_edges = set()
        for node in nodes:
            for edge in node.edges:
                # Add tuple of node IDs to set to avoid duplicate edges
                edge_key = tuple(sorted([edge.lnode.id, edge.rnode.id]))
                all_edges.add((edge_key, edge))
                
        # Add links for each unique edge
        for (_, edge) in all_edges:
            lnode = switch_host_dic[edge.lnode.id]
            rnode = switch_host_dic[edge.rnode.id]
            self.addLink(lnode, rnode, bw=15, delay='5ms')
            count += 1
            # print(f"Adding link between {lnode} and {rnode}")
            
        print(f"Added {count} links")
        
        # (Optional) Now safely remove all edges since we're done adding links
        for (_, edge) in all_edges:
            edge.remove()

        # TODO: Richtige Ip-Adressen und Subnetze für die Hosts setzen und berechenn
        # TODO: please complete the network generation logic here
        
def ip_to_dpid(ip_with_cidr):
    # Strip /24 (or any subnet)
    ip = ip_with_cidr.split('/')[0]
    
    # Convert IP to integer
    ip_int = int(ipaddress.IPv4Address(ip))
    
    # Convert to 16-character hex (DPID must be 8 bytes = 16 hex chars)
    dpid = f'{ip_int:016x}'
    
    return dpid

def make_mininet_instance(graph_topo):

    net_topo = FattreeNet(graph_topo)
    net = Mininet(topo=net_topo, controller=None, autoSetMacs=True, link=TCLink)
    net.addController('c0', controller=RemoteController,
                      ip="127.0.0.1", port=6653)
    return net

def run(graph_topo):

    # Run the Mininet CLI with a given topology
    lg.setLogLevel('info')
    net = make_mininet_instance(graph_topo)
    
    print("\n*** Switches and their DPIDs:")
    for sw in net.switches:
        print(f"{sw.name} => DPID: {sw.dpid}")

    info('*** Starting network ***\n')
    net.start()
    info('*** Running CLI ***\n')
    CLI(net)
    info('*** Stopping network ***\n')
    net.stop()
    mininet.clean.cleanup()

if __name__ == '__main__':
    ft_topo = Fattree(4)
    run(ft_topo)
    