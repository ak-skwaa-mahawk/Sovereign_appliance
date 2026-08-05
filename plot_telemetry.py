import json
import matplotlib.pyplot as plt

try:
    with open("mesh_telemetry.json", "r") as f:
        data = json.load(f)
except FileNotFoundError:
    print("Error: 'mesh_telemetry.json' not found. Run 'python3 mesh_sim.py' first.")
    exit(1)

nodes = data["final_node_matrix"]

plt.figure(figsize=(10, 6))
plt.style.use('dark_background')

node_names = list(nodes.keys())
reputations = [nodes[n]["reputation"] for n in node_names]

x = range(len(node_names))

plt.bar(x, reputations, color='skyblue', alpha=0.7, label='Reputation Score')
plt.title("DePIN Mesh Network - Final Node Performance")
plt.xlabel("Mesh Nodes")
plt.ylabel("Reputation Points")
plt.xticks(x, node_names)
plt.axhline(y=100.0, color='r', linestyle='--', label='Baseline Rep (100.0)')
plt.grid(True, linestyle=':', alpha=0.4)
plt.legend(loc="lower right")
plt.tight_layout()

output_png = "reputation_chart.png"
plt.savefig(output_png, dpi=300)

print("\n===========================================================")
print(f" [SUCCESS]: Visual chart exported to '{output_png}'")
print("===========================================================")
