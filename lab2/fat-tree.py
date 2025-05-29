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
                id = switch.id
                pod_id = id[3]
                switch_id = id[5]
                num_id = id[7]
                switch_ip = f"10.{pod_id}.{switch_id}.{num_id}/24"
                new_switch = self.addSwitch(switch.id)
                switch_host_dic[switch.id] = new_switch
                count+=1
                print(f"Adding core switch {switch.id} with IP {switch_ip}")
            else:
                # pod switches
                id = switch.id
                pod_id = id[3]
                switch_id = id[5]
                num_id = id[7]
                switch_ip = f"10.{pod_id}.{switch_id}.{num_id}/24"
                new_switch = self.addSwitch(switch.id)
                switch_host_dic[switch.id] = new_switch
                count += 1
                print(f"Adding pod switch {switch.id} with IP {switch_ip}")
        print(f"Added {count} switches")

        count = 0
        for server in servers:
            id = server.id
            # Extracting the pod, switch, and host IDs from the server ID
            # A bit primitive, but works for the given format for the moment 
            # TODO: Make it a bit prettier :D --> Shit, the names from topo are allowed to be named after "pod_switch_host" with lower bindings...
            pod_id = id[4]
            switch_id = id[6]
            host_id = id[8]
            server_ip = f"10.{pod_id}.{switch_id}.{host_id}/24" 
            # TODO: Default Route??? -> Set to corresponding lower level switch
            new_host = self.addHost(server.id, ip=server_ip, defaultRoute='via 10.0.1.1')
            switch_host_dic[server.id] = new_host
            count += 1
            print(f"Adding server {server.id} with IP {switch_ip}")
        print(f"Added {count} servers")

        nodes = []
        nodes.extend(switches)
        nodes.extend(servers) # optional: if all edges of switches are set, servers will be connected
        count = 0
        for node in nodes:
            for edge in node.edges:
                lnode = switch_host_dic[edge.lnode.id]
                rnode = switch_host_dic[edge.rnode.id]
                self.addLink(lnode, rnode, bw=15, delay='10ms')
                node.remove_edge(edge)
                count += 1
                print(f"Adding link between {lnode} and {rnode}")
        print(f"Added {count} links")

        # TODO: Verbindungen zwischen den Switches und Hosts erstellen
        # TODO: Richtige Ip-Adressen und Subnetze für die Hosts setzen und berechenn
        # TODO: please complete the network generation logic here



def make_mininet_instance(graph_topo):

    net_topo = FattreeNet(graph_topo)
    net = Mininet(topo=net_topo, controller=None, autoSetMacs=True)
    net.addController('c0', controller=RemoteController,
                      ip="127.0.0.1", port=6653)
    return net


def run(graph_topo):

    # Run the Mininet CLI with a given topology
    lg.setLogLevel('info')
    mininet.clean.cleanup()
    net = make_mininet_instance(graph_topo)

    info('*** Starting network ***\n')
    net.start()
    info('*** Running CLI ***\n')
    CLI(net)
    info('*** Stopping network ***\n')
    net.stop()


if __name__ == '__main__':
    ft_topo = Fattree(4)
    run(ft_topo)