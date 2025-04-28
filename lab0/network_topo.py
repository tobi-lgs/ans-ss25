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

# see https://mininet.org/walkthrough/

#!/usr/bin/python

from mininet.cli import CLI
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.node import Controller
# from mininet.node import RemoteController # using ovs-testcontroller or ryu controller
from mininet.node import OVSController #  sudo apt-get install openvswitch-testcontroller

class BridgeTopo(Topo):
    "Creat a bridge-like customized network topology according to Figure 1 in the lab0 description."

    def __init__(self):

        Topo.__init__(self)

        # TODO: add nodes and links to construct the topology; remember to specify the link properties
        h1 = self.addHost('h1', ip='10.0.0.1')
        h2 = self.addHost('h2', ip='10.0.0.2')
        h3 = self.addHost('h3', ip='10.0.0.3')
        h4 = self.addHost('h4', ip='10.0.0.4')

        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')

        self.addLink(h1, s1, bw=15, delay='10ms')
        self.addLink(h2, s1, bw=15, delay='10ms')
        self.addLink(h3, s2, bw=15, delay='10ms')
        self.addLink(h4, s2, bw=15, delay='10ms')
        self.addLink(s1, s2, bw=20, delay='45ms')

# if using >> sudo -E mn --custom /vagrant/lab0/network_topo.py --topo bridge --link tc <<
topos = {'bridge': (lambda: BridgeTopo())}

if __name__ == '__main__':
    topo = BridgeTopo()

    net = Mininet(topo=topo)
#     # net = Mininet(topo=topo, link=TCLink)
#     # net = Mininet(topo=topo, link=TCLink, controller=OVSController)
#     net = Mininet(topo=topo, link=TCLink, controller=Controller) # not installed
#     # net = Mininet(topo=topo, link=TCLink) # not working without controller

    net.start()
    
    CLI( net )

    net.stop()

# sudo fuser -k 6653/tcp