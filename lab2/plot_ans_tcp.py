import matplotlib.pyplot as plt
import pandas as pd




data = {
    "Routing": ["SP", "FT", "SP", "FT"],
    "Client": ["10.0.0.2", "10.0.0.2", "10.0.0.3", "10.0.0.3"],
    "Server": ["10.2.1.2", "10.2.1.2", "10.2.1.3", "10.2.1.3"],
    "Protocol": ["TCP", "TCP", "TCP", "TCP"],
    "Transfer [MBytes]": [24.6, 40.2, 20.8, 43.8],
    "Bandwidth [Mbits/s]": [8.97, 16.7, 7.79, 16.3],
}


df = pd.DataFrame(data)

plt.figure(figsize=(10, 6))
bar_width = 0.35
x_labels = df['Client'] + "\n" + df['Server']
unique_labels = list(dict.fromkeys(x_labels)) 
x_pos = list(range(len(unique_labels)))
routing_types = df['Routing'].unique()

for i, routing in enumerate(routing_types):
    routing_df = df[df['Routing'] == routing]
    values = []
    for label in unique_labels:
        match = routing_df[(routing_df['Client'] + "\n" + routing_df['Server']) == label]
        values.append(match["Bandwidth [Mbits/s]"].values[0] if not match.empty else 0)
    plt.bar([p + i * bar_width for p in x_pos], values, width=bar_width, label=routing)

plt.xlabel("Client - Server")
plt.ylabel("Bandbreite [Mbit/s]")
plt.title("iperf TCP simultaneous - Ergebnisse")
plt.xticks([p + bar_width / 2 for p in x_pos], unique_labels)
plt.legend(title="Routing")
plt.grid(True, axis='y')
plt.tight_layout()

#plt.show()
plt.savefig("iperf_tcp_results.png", dpi=300, bbox_inches='tight')