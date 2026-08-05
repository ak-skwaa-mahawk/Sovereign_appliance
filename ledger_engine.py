import sqlite3
import json
import hashlib
import time
import numpy as np

DB_FILE = "sovereign_ledger.db"
REACTION_RATE_K = 0.05  # Rejection decay threshold

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS blocks
                 (block_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp REAL,
                  leaf_count INTEGER,
                  yield_ratio REAL,
                  merkle_root TEXT,
                  payload_json TEXT)''')
    conn.commit()
    conn.close()

def compute_merkle_root(leaves):
    if not leaves:
        return hashlib.sha256(b"").hexdigest()
    current_level = [hashlib.sha256(leaf.encode('utf-8')).hexdigest() for leaf in leaves]
    while len(current_level) > 1:
        if len(current_level) % 2 != 0:
            current_level.append(current_level[-1])
        next_level = []
        for i in range(0, len(current_level), 2):
            combined = current_level[i] + current_level[i+1]
            next_level.append(hashlib.sha256(combined.encode('utf-8')).hexdigest())
        current_level = next_level
    return current_level[0]

def evaluate_mesh_yield(frame):
    """
    Calculates the Telemetry Yield Ratio Phi_mesh.
    Rejects noisy frames (analogous to RF interference).
    """
    max_amp = frame.get('max_amplitude', 0.0)
    min_amp = frame.get('min_amplitude', 0.0)
    energy = frame.get('total_energy', 0.0)
    
    # Validation Gate: Check non-negativity and bounded energy
    if min_amp < -1e-6 or energy <= 0 or np.isnan(max_amp):
        return 0.0  # RF Scramble / Corrupted Frame
    
    # Effective frequency offset metric
    omega_eff = abs(max_amp - 1.0)
    phi_mesh = 0.5 + 0.5 * (REACTION_RATE_K**2 / (REACTION_RATE_K**2 + omega_eff**2))
    return phi_mesh

def commit_telemetry_batch(telemetry_file="mesh_telemetry.json"):
    try:
        with open(telemetry_file, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Failed to read telemetry file: {e}")
        return None

    raw_frames = data.get("frames", [])
    valid_leaves = []
    yield_scores = []

    for frame in raw_frames:
        phi = evaluate_mesh_yield(frame)
        if phi > 0.5:  # Coherence threshold gate
            frame['yield_score'] = phi
            valid_leaves.append(json.dumps(frame, sort_keys=True))
            yield_scores.append(phi)
        else:
            print(f"⚠️ Dropped incoherent frame: {frame.get('type')}")

    if not valid_leaves:
        print("❌ No coherent frames passed yield filter.")
        return None

    root = compute_merkle_root(valid_leaves)
    avg_yield = float(np.mean(yield_scores))
    timestamp = time.time()

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''INSERT INTO blocks (timestamp, leaf_count, yield_ratio, merkle_root, payload_json)
                 VALUES (?, ?, ?, ?, ?)''', (timestamp, len(valid_leaves), avg_yield, root, json.dumps(data)))
    block_id = c.lastrowid
    conn.commit()
    conn.close()

    print(f"✅ Committed Block #{block_id} | Yield Ratio: {avg_yield:.4f} | Merkle Root: {root}")
    return root

if __name__ == "__main__":
    init_db()
    commit_telemetry_batch()
