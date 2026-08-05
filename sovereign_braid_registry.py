import numpy as np
import cmath
import sqlite3
import hashlib
import json
import time

# ==============================================================================
# 1. EXACT UNITARY FIBONACCI BRAID GENERATORS
# ==============================================================================
PHI = (1.0 + np.sqrt(5.0)) / 2.0

# Exact Unitary Fibonacci F-Matrix
# F = [[1/PHI, 1/sqrt(PHI)], [1/sqrt(PHI), -1/PHI]]
F = np.array([
    [1.0 / PHI, 1.0 / np.sqrt(PHI)],
    [1.0 / np.sqrt(PHI), -1.0 / PHI]
], dtype=complex)

# R-Symbols
R1 = cmath.exp(-4j * np.pi / 5.0)
R_TAU = cmath.exp(3j * np.pi / 5.0)
R = np.diag([R1, R_TAU])

# Generators
B1 = np.diag([R1, R_TAU, R_TAU])
B2 = np.block([
    [np.array([[R1]]), np.zeros((1, 2), dtype=complex)],
    [np.zeros((2, 1), dtype=complex), F @ R @ F]
])
B3 = np.diag([R_TAU, R_TAU, R1])

GENERATOR_MAP = {
    'B1': B1, 'B1_inv': B1.conj().T,
    'B2': B2, 'B2_inv': B2.conj().T,
    'B3': B3, 'B3_inv': B3.conj().T
}

def evaluate_braid_word(word_sequence, initial_state=None):
    if initial_state is None:
        initial_state = np.array([1.0, 0.0, 0.0], dtype=complex)
    
    operator_chain = np.eye(3, dtype=complex)
    for op_name in word_sequence:
        U = GENERATOR_MAP[op_name]
        operator_chain = U @ operator_chain
        
    current_state = operator_chain @ initial_state
    densities = np.abs(current_state) ** 2
    phase = np.angle(np.sum(current_state))
    return current_state, densities, phase, operator_chain

if __name__ == "__main__":
    braid_word = ['B1', 'B2', 'B3', 'B2_inv', 'B1']
    final_state, densities, phase, U_total = evaluate_braid_word(braid_word)
    
    # Exact Matrix Unitarity check: || U^\dagger U - I ||
    unitarity_residual = float(np.linalg.norm(U_total.conj().T @ U_total - np.eye(3)))
    
    payload = {
        "type": "braid_registry_op",
        "braid_word": braid_word,
        "state_densities": densities.tolist(),
        "phase_rad": phase,
        "unitarity_residual": unitarity_residual,
        "timestamp": time.time()
    }
    
    payload_json = json.dumps(payload, sort_keys=True)
    merkle_root = hashlib.sha256(payload_json.encode('utf-8')).hexdigest()
    
    with open("mesh_telemetry.json", "w") as f:
        json.dump({"frames": [payload]}, f, indent=2)
    
    conn = sqlite3.connect('sovereign_ledger.db')
    c = conn.cursor()
    yield_ratio = float(1.0 - unitarity_residual)
    c.execute('''INSERT INTO blocks (timestamp, leaf_count, yield_ratio, merkle_root, payload_json)
                 VALUES (?, ?, ?, ?, ?)''', (time.time(), len(braid_word), yield_ratio, merkle_root, payload_json))
    block_id = c.lastrowid
    conn.commit()
    conn.close()
    
    print(f"🌀 Braid Sequence Evaluated: {' -> '.join(braid_word)}")
    print(f"   Final State Densities (|v1|², |v2|², |v3|²): {np.round(densities, 6)}")
    print(f"   Global Phase Angle: {phase:.6f} rad")
    print(f"   Unitarity Residual: {unitarity_residual:.2e}")
    print(f"✅ Inscribed Block #{block_id} (Braid Registry Op)")
    print(f"   Yield Ratio: {yield_ratio:.6f} | Merkle Root: {merkle_root}")
