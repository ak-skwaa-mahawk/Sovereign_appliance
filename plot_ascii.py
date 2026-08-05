import json

try:
    with open("mesh_telemetry.json", "r") as f:
        data = json.load(f)
except FileNotFoundError:
    print("Error: 'mesh_telemetry.json' not found. Run 'python3 mesh_sim.py' first.")
    exit(1)

nodes = data["final_node_matrix"]

print("\n===========================================================")
print("         DePIN MESH NETWORK - FINAL REPUTATION CHART       ")
print("===========================================================\n")

for name, info in nodes.items():
    rep = info["reputation"]
    relays = info["successful_relays"]
    fails = info["failed_relays"]
    
    # Scale reputation score to ASCII bar length
    bar_units = int((rep - 95.0) * 3) if rep >= 95.0 else 1
    bar = "█" * max(1, bar_units)
    
    print(f"Node {name:<7} [{rep:>5.1f} Rep] | {bar}")
    print(f"         └── Relays: {relays} Success / {fails} Failed\n")

print("===========================================================")
