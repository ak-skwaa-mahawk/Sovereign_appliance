import json

try:
    with open("mesh_telemetry.json", "r") as f:
        data = json.load(f)
except FileNotFoundError:
    print("Error: 'mesh_telemetry.json' not found. Run 'python3 mesh_sim.py' first.")
    exit(1)

nodes = data["final_node_matrix"]
node_names = list(nodes.keys())
reputations = [nodes[n]["reputation"] for n in node_names]
success_relays = [nodes[n]["successful_relays"] for n in node_names]
failed_relays = [nodes[n]["failed_relays"] for n in node_names]

# Extract cycle latency data from events
cycle_labels = [f"Cycle {c['cycle']}" for c in data["cycles"]]
payload_sizes = [c["message"]["payload_bytes"] for c in data["cycles"]]

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DePIN Mesh Network Telemetry Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-color: #f8fafc;
            --accent-blue: #38bdf8;
            --accent-green: #4ade80;
            --accent-red: #f87171;
            --border-color: #334155;
        }}
        body {{
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 16px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 24px;
        }}
        .header h1 {{
            font-size: 1.5rem;
            margin: 0 0 8px 0;
            color: var(--accent-blue);
        }}
        .header p {{
            font-size: 0.85rem;
            color: #94a3b8;
            margin: 0;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 16px;
            max-width: 900px;
            margin: 0 auto;
        }}
        .card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        }}
        .card h2 {{
            font-size: 1.1rem;
            margin-top: 0;
            margin-bottom: 12px;
            color: #e2e8f0;
        }}
        .chart-container {{
            position: relative;
            height: 260px;
            width: 100%;
        }}
        .stats-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
            margin-top: 8px;
        }}
        .stats-table th, .stats-table td {{
            padding: 8px 10px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}
        .stats-table th {{
            color: #94a3b8;
            font-weight: 600;
        }}
        .badge {{
            display: inline-block;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: bold;
        }}
        .badge-success {{ background: rgba(74, 222, 128, 0.2); color: var(--accent-green); }}
        .badge-fail {{ background: rgba(248, 113, 113, 0.2); color: var(--accent-red); }}
    </style>
</head>
<body>

    <div class="header">
        <h1>DePIN Mesh Network Dashboard</h1>
        <p>Real-Time Node Telemetry & Cryptographic Verification Engine</p>
    </div>

    <div class="grid">
        <!-- Reputation Chart -->
        <div class="card">
            <h2>Node Reputation Metrics (Ed25519 Verified)</h2>
            <div class="chart-container">
                <canvas id="repChart"></canvas>
            </div>
        </div>

        <!-- Relay Statistics Chart -->
        <div class="card">
            <h2>Relay Performance (Success vs Failures)</h2>
            <div class="chart-container">
                <canvas id="relayChart"></canvas>
            </div>
        </div>

        <!-- Node Matrix Table -->
        <div class="card">
            <h2>Final Node Matrix Summary</h2>
            <div style="overflow-x:auto;">
                <table class="stats-table">
                    <thead>
                        <tr>
                            <th>Node</th>
                            <th>Reputation</th>
                            <th>Successful Relays</th>
                            <th>Failed Relays</th>
                            <th>Interfaces</th>
                        </tr>
                    </thead>
                    <tbody>
"""

for name in node_names:
    n = nodes[name]
    interfaces = ", ".join(n["supported_interfaces"])
    html_content += f"""
                        <tr>
                            <td><strong>Node {name}</strong></td>
                            <td><span class="badge badge-success">{n['reputation']}</span></td>
                            <td>{n['successful_relays']}</td>
                            <td>{n['failed_relays']}</td>
                            <td style="color: #94a3b8;">{interfaces}</td>
                        </tr>
    """

html_content += f"""
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        const darkThemeOptions = {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ labels: {{ color: '#94a3b8', font: {{ size: 11 }} }} }}
            }},
            scales: {{
                x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#334155' }} }},
                y: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#334155' }} }}
            }}
        }};

        // Reputation Bar Chart
        new Chart(document.getElementById('repChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(node_names)},
                datasets: [{{
                    label: 'Reputation Score',
                    data: {json.dumps(reputations)},
                    backgroundColor: 'rgba(56, 189, 248, 0.75)',
                    borderColor: '#38bdf8',
                    borderWidth: 1,
                    borderRadius: 4
                }}]
            }},
            options: {{
                ...darkThemeOptions,
                scales: {{
                    ...darkThemeOptions.scales,
                    y: {{ ...darkThemeOptions.scales.y, min: 95, max: 112 }}
                }}
            }}
        }});

        // Relay Success vs Fail Chart
        new Chart(document.getElementById('relayChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(node_names)},
                datasets: [
                    {{
                        label: 'Successful Relays',
                        data: {json.dumps(success_relays)},
                        backgroundColor: 'rgba(74, 222, 128, 0.75)',
                        borderColor: '#4ade80',
                        borderWidth: 1,
                        borderRadius: 4
                    }},
                    {{
                        label: 'Failed Relays',
                        data: {json.dumps(failed_relays)},
                        backgroundColor: 'rgba(248, 113, 113, 0.75)',
                        borderColor: '#f87171',
                        borderWidth: 1,
                        borderRadius: 4
                    }}
                ]
            }},
            options: darkThemeOptions
        }});
    </script>
</body>
</html>
"""

with open("dashboard.html", "w") as f:
    f.write(html_content)

print("\n===========================================================")
print(" [SUCCESS]: Interactive dashboard generated -> 'dashboard.html'")
print(" Launching mobile browser via termux-open...")
print("===========================================================\n")
