import matplotlib.pyplot as plt
import pandas as pd

data = {
    "Routing": ["SP", "SP", "FT", "FT"],
    "Client": ["10.0.0.2", "10.0.0.3", "10.0.0.2", "10.0.0.3"],
    "Server": ["10.2.1.2", "10.2.1.3", "10.2.1.2", "10.2.1.3"],
    "Protocol": ["UDP", "UDP", "UDP", "UDP"],
    "Transfer [MBytes]": [37.5, 37.5, 37.5, 37.5],
    "Bandwidth [Mbits/s]": [15, 15, 15, 15],
    "Jitter [ms]": [1.384, 1.092, 0.698, 1.173],
    "Lost/Total [%]": [54, 53, 13, 13]
}

df = pd.DataFrame(data)
df["Pair"] = df["Client"] + "\n" + df["Server"]

df = df.sort_values(by=["Pair", "Routing"])
pairs = df["Pair"].unique()
bar_width = 0.35
x = list(range(len(pairs)))

fig, ax = plt.subplots(figsize=(10, 6))

colors = {
    "SP": "orange",
    "FT": "red"
}

for i, routing in enumerate(["SP", "FT"]):
    sub_df = df[df["Routing"] == routing]
    offset = (-0.5 + i) * bar_width

    ax.bar(
        [j + offset for j in x],
        sub_df["Lost/Total [%]"],
        width=bar_width,
        label=f"{routing} Lost/Total",
        color=colors[routing]
    )

ax.set_ylabel("Lost/Total [%]")
ax.set_xlabel("Client - Server")
ax.set_xticks(x)
ax.set_xticklabels(pairs)
ax.grid(axis='y')
plt.title("iperf UDP - Paketverlust nach Routing")
plt.legend(loc="upper right")
plt.tight_layout()
#plt.show()
plt.savefig('iperf_udp_packet_loss.png', dpi=300, bbox_inches='tight')