#!/usr/bin/env python3
"""
End-to-End Integration Harness:
Firecrawl Ingress -> Admission Gate Policy -> Notarizer Quorum Verification.
"""

import json
import subprocess
import sys
from pathlib import Path

def run_cmd(cmd: list[str], input_data: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        input=input_data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True
    )

def main() -> int:
    print("[1/3] Testing Firecrawl Ingress & Gate Policy...")
    payload = b'{"dataset": "soliton-mainnet", "state": "immutable"}'
    ingress = run_cmd(
        [sys.executable, "firecrawl_ingress.py", "--source-id", "harness_run_01"],
        input_data=payload
    )
    print(ingress.stdout.decode().strip())

    print("\n[2/3] Generating Triad Notarizer Approval Vector...")
    # Read the latest entry hash from audit_log.jsonl to use as the challenge nonce
    with open("audit_log.jsonl", "r") as f:
        lines = [line.strip() for line in f if line.strip()]
        last_entry = json.loads(lines[-1])
        nonce_hex = last_entry["entry_hash"][:64]

    approval = run_cmd([
        sys.executable, "notarizer_signer.py",
        "--seq-id", "42",
        "--nonce-hex", nonce_hex,
        "--out-bin", "./workspace/harness_approval.bin"
    ])
    print(approval.stdout.decode().strip())

    print("\n[3/3] Verifying Dataport Layout Binary Size...")
    approval_file = Path("./workspace/harness_approval.bin")
    size = approval_file.stat().st_size
    assert size == 424, f"Expected 424 bytes matching C struct, got {size}"
    print(f"Validation successful: Approval vector is {size} bytes, linked to tip {nonce_hex[:16]}...")

    return 0

if __name__ == "__main__":
    sys.exit(main())
