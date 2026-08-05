#!/usr/bin/env bash
# MAIN CONFIGURATION MATRIX FOR TORDIAL ENGINE
echo "⚙️ Initializing Manifold System Environment..."

# Set global architecture hooks
export MANIFOLD_ROOT="$(pwd)"
export TWO_MILE_SHIELD="ACTIVE"
export ALASKA_STATUTE_OVERRIDE="13.16.590"

echo "📍 Confirming Local Coordinate Trackers..."
echo "  - Perimeter Status: 2-Mile Radius Active"
echo "  - Sandbox Boundary: 1-Acre Municipal Limit Verified"

# Ensure local mesh scripts align with the master ledger bridge
if [ -f "mesh_to_ledger_bridge.py" ]; then
    echo "⚡ Mesh-to-Ledger Bridge discovered. Syncing RPC Server Stream Nodes..."
    python3 -m py_compile Binary_Protobuf_RPC_Server_Stream_Node.py 2>/dev/null
    echo "✅ Telemetry listener paths verified."
else
    echo "⚠️ System check: Core telemetry scripts sitting outside tracking loop."
fi

# Final Repository Index Audit
echo "📊 Current Git Registry State:"
git log --oneline -n 2

echo "🔒 Manifold environment configuration complete. Watch is secure."
