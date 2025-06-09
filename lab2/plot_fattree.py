import matplotlib.pyplot as plt
import networkx as nx
from topo import Fattree
import math


def plot_fattree(ft_topo, k):

    G = nx.Graph()
    color_map = []
    pos = {}

    # Y-Achse: Core ganz oben (y=0), Server ganz unten (y=3)
    layer_mapping = {
    'core': 0,
    'aggregation': 1,
    'edge': 2,
    'server': 3
    }

    # Gruppiere Nodes nach Layer, um sie besser zu platzieren
    layer_nodes = {l: [] for l in layer_mapping}

    for node in ft_topo.servers + ft_topo.switches:
        if node.type == 'server':
            layer_nodes['server'].append(node)
            color_map.append('lightblue')
        elif node.type == 'edge_level_switch':
            layer_nodes['edge'].append(node)
            color_map.append('green')
        elif node.type == 'aggregation_switch':
            layer_nodes['aggregation'].append(node)
            color_map.append('orange')
        elif node.type == 'core_switch':
            layer_nodes['core'].append(node)
            color_map.append('red')
        else:
            continue

        G.add_node(node.id)

    # Manuelle Positionierung: gleichmäßige Verteilung pro Layer, zentriert
    max_count = max(len(nodes) for nodes in layer_nodes.values())
    spacing = 20  # X-Abstand (increased for more inter-pod spacing)

    for layer, nodes in layer_nodes.items():
        y = -layer_mapping[layer]
        count = len(nodes)
        if count == 0:
            continue
        total_width = (count - 1) * spacing
        max_total_width = (max_count - 1) * spacing
        start_x = (max_total_width - total_width) / 2  # Zentrierung
        for i, node in enumerate(sorted(nodes, key=lambda n: n.id)):
            x = start_x + i * spacing
            pos[node.id] = (x, y)

    # Kanten hinzufügen
    added = set()
    for node in ft_topo.servers + ft_topo.switches:
        for edge in node.edges:
            a, b = edge.lnode.id, edge.rnode.id
            link = tuple(sorted([a, b]))
            if link not in added:
                G.add_edge(a, b)
                added.add(link)

    plt.figure(figsize=(max(10, len(G.nodes) * 0.4), 6))
    nx.draw(G, pos, with_labels=True, node_color=color_map, node_size=700, font_size=7)
    plt.title(f"Fat-Tree Topology (k={k})")
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(f"fattree_k{k}.pdf", format="pdf")
    plt.savefig(f"fattree_k{k}.png")
    print(f"[✓] Grafik gespeichert: fattree_k{k}.png")

if __name__ == "__main__":
    for k in [2, 4, 6]:
        ft = Fattree(k)
        plot_fattree(ft, k)