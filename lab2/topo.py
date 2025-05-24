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

# Class for an edge in the graph
class Edge:
	def __init__(self):
		self.lnode = None
		self.rnode = None
	
	def remove(self):
		self.lnode.edges.remove(self)
		self.rnode.edges.remove(self)
		self.lnode = None
		self.rnode = None

# Class for a node in the graph
class Node:
	def __init__(self, id, type):
		self.edges = []
		self.id = id
		self.type = type

	# Add an edge connected to another node
	def add_edge(self, node):
		edge = Edge()
		edge.lnode = self
		edge.rnode = node
		self.edges.append(edge)
		node.edges.append(edge)
		return edge

	# Remove an edge from the node
	def remove_edge(self, edge):
		self.edges.remove(edge)

	# Decide if another node is a neighbor
	def is_neighbor(self, node):
		for edge in self.edges:
			if edge.lnode == node or edge.rnode == node:
				return True
		return False


class Fattree:

	def __init__(self, num_ports):
		self.servers = []
		self.switches = []
		self.generate(num_ports)

	def generate(self, num_ports):
		# claculate number of switches for overview
		pods = num_ports
		switches_per_pod = num_ports
		num_core_switches = num_ports**2 // 4

		# create core switches
		number_of_switches = pods * switches_per_pod + num_core_switches
		# number of hosts from paper
		#number_of_servers = num_ports**3/4

		# number of hosts from thoughts
		number_of_servers = (switches_per_pod/2) * (num_ports/2) * pods
		# core switches naming: cs1, cs2, ...
		# create core switches
		core_switches = []
		for i in range(num_core_switches):
			switch = Node(id=f'cs{i+1}', type='core_level_switch')
			core_switches.append(switch)
        # TODO: Changwe names (servers;switches) to our style???
		# create pod
		# topology idea: [upperlayer_switches_pod1, lower_layer_switches_pod1, ...,upperlayer_switches_podk, lower_layer_switches_podk, core_switches] for number of switches in pod
		for pod in range(pods):
			upper_layer_switches = []
			lower_layer_switches = []
			server_in_pod = []
			# create upper layer switches:
			for i in range(switches_per_pod/2):
				# upper layer switches naming: usp1s1, usp1s2, ...
				upper_switch = Node(id=f'usp{pod+1}s{i+1}', type='upper_level_switch')
				# connect upper layer switches to core switches
				for j in range(num_ports/2):
					upper_switch.add_edge(core_switches[j*i])
				upper_layer_switches.append(upper_switch)
			
			# seperated for readability (could be done in one loop)
			# create lower layer switches:
			for i in range(switches_per_pod / 2):
				# lower layer switches naming: ls1, ls2, ...
				# alternatively maybe: lsp1s(i*2+1) ??? --> ask tobi and niklas
				switch = Node(id=f'lsp{pod+1}s{i+1}', type='lower_level_switch')
				for host in range(num_ports/2):
					server = Node(id=f'serp{pod+1}s{i+1}h{host+1}', type='server')
					server.add_edge(switch)
					server_in_pod.append(server)
				# connnect lower and upper layer switches in pod
				for upper_switch in upper_layer_switches:
					switch.add_edge(upper_switch)
            
				lower_layer_switches.append(switch)
			self.servers.extend(server_in_pod)
			self.switches.extend(upper_layer_switches)
			self.switches.extend(lower_layer_switches)
		self.switches.extend(core_switches)
	# calculate number of servers/hosts
	# number_of_servers = num_ports/2 * pods

	# TODO: code for generating the fat-tree topology