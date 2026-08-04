import json
from datetime import datetime
from typing import List, Dict
from pathlib import Path

REGISTRY_FILE = Path("soliton_registry.jsonl")

class BraidOpLogger:
    """Sovereign logging for braid operations on lineage."""
    def __init__(self, registry_path: Path = REGISTRY_FILE):
        self.path = registry_path

    def log_braid_op(self, session_id: str, braid_word: List[Dict], before_state: Dict, after_state: Dict):
        """Log braid transformation as sovereign entry."""
        entry = {
            "entry_type": "BRAID_OP",
            "timestamp_utc": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "braid_word": braid_word,
            "before": {
                "events_order": before_state["events"],
                "fusion_path": before_state["fusion_path"]
            },
            "after": {
                "events_order": after_state["events"],
                "fusion_path": after_state["fusion_path"]
            },
            "status": "LINEAGE_TRANSFORMED"
        }

        # Hash for integrity
        canonical = json.dumps(entry, sort_keys=True)
        entry["hash"] = hashlib.sha256(canonical.encode()).hexdigest()

        with self.path.open("a") as f:
            f.write(json.dumps(entry) + "\n")

        print(f"BraidOp Logged | Session: {session_id} | Word: {braid_word}")
        print(f"  Before → After: {before_state['events']} → {after_state['events']}")
        return entry["hash"]
{
  "entry_type": "VITALITY_AGGREGATE",
  "timestamp_utc": "2025-12-25T20:13:42.918273",
  "snh_digest": "a3f1c0e2d9b4f7a1c8e0d1b2f3a4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b",
  "packet_hash": "a3f1c0e2d9b4f7a1c8e0d1b2f3a4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b",
  "payload_summary": {
    "vitality": 1.12,
    "coherence": 0.84,
    "node_count": 4
  },
  "revoked": false
}
{
  "entry_type": "BRAID_OP",
  "timestamp_utc": "2025-12-25T21:00:00",
  "session_id": "session-τ-001",
  "braid_word": [
    {"generator": "B2", "exponent": 1},
    {"generator": "B1", "exponent": 1},
    {"generator": "B2", "exponent": 1}
  ],
  "before": {
    "events_order": ["E1", "E2", "E3"],
    "fusion_path": [0]
  },
  "after": {
    "events_order": ["E3", "E2", "E1"],
    "fusion_path": [1]
  },
  "status": "LINEAGE_TRANSFORMED",
  "hash": "abc123..."
}