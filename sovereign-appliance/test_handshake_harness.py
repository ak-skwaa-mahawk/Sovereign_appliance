#!/usr/bin/env python3
import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from ingress_firewall import inspect_ingress

def run_cmd(cmd, input_data=None):
    res = subprocess.run(
        cmd,
        input=input_data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True if isinstance(input_data, str) or input_data is None else False
    )
    stdout_txt = res.stdout if isinstance(res.stdout, str) else res.stdout.decode('utf-8', errors='replace')
    stderr_txt = res.stderr if isinstance(res.stderr, str) else res.stderr.decode('utf-8', errors='replace')

    if res.returncode != 0:
        print(f"[-] Command failed: {' '.join(cmd)}", file=sys.stderr)
        print(f"[-] Exit code: {res.returncode}", file=sys.stderr)
        print(f"[-] STDOUT:\n{stdout_txt}", file=sys.stderr)
        print(f"[-] STDERR:\n{stderr_txt}", file=sys.stderr)
        sys.exit(res.returncode)
    return stdout_txt

def acquire_payload(args):
    """Acquires ingestion payload from stdin, file, inline JSON, or falls back to mock."""
    if args.stdin:
        raw = sys.stdin.buffer.read()
        if not raw:
            raise ValueError("Standard input requested but received 0 bytes.")
        return raw, "stream_stdin"
    elif args.payload_file:
        p = Path(args.payload_file)
        if not p.exists():
            raise FileNotFoundError(f"Payload file not found: {args.payload_file}")
        return p.read_bytes(), p.stem
    elif args.payload_json:
        return args.payload_json.encode('utf-8'), f"inline_{int(time.time())}"
    else:
        # Default mock mode for automated smoke tests
        default_mock = b'{"url": "https://sovereign.local/audit", "content": "admission test telemetry", "depth": 1}'
        return default_mock, "harness_run_01"

def main():
    parser = argparse.ArgumentParser(description="Sovereign Appliance Dynamic Ingress & Dataport Notarizer")
    parser.add_argument("--stdin", action="store_true", help="Ingest raw payload directly from stdin")
    parser.add_argument("--payload-file", type=str, default=None, help="Path to input payload file")
    parser.add_argument("--payload-json", type=str, default=None, help="Inline JSON string payload")
    parser.add_argument("--source-id", type=str, default=None, help="Explicit ingestion source identifier")
    parser.add_argument("--seq-id", type=int, default=None, help="Monotonic sequence ID (defaults to 42 for harness fallback)")
    parser.add_argument("--risk-tier", type=str, choices=["1", "2", "3"], default="1", help="Gate risk tier assignment")
    args = parser.parse_args()

    try:
        payload_bytes, auto_source_id = acquire_payload(args)
    except Exception as e:
        print(f"[-] Ingress Acquisition Error: {e}", file=sys.stderr)
        return 1

    source_id = args.source_id or auto_source_id
    seq_id = args.seq_id if args.seq_id is not None else 42

    # Ingress Security Firewall Pre-Flight Evaluation
    payload_str = payload_bytes.decode("utf-8", errors="replace")
    context_desc = f"Ingress Stream [{source_id}]"
    if not inspect_ingress(context_desc, payload_str, {"frame_size": 424, "seq_id_bits": 32}):
        print("[-] Ingress firewall rejection: Payload or frame layout violation", file=sys.stderr)
        return 1

    print(f"[1/3] Testing Ingress & Gate Policy for '{source_id}' ({len(payload_bytes)} bytes)...")
    ingress_out = run_cmd([
        sys.executable,
        "firecrawl_ingress.py",
        "--source-id", source_id,
        "--risk-tier", args.risk_tier
    ], input_data=payload_bytes)
    print(ingress_out.strip())

    print("\n[2/3] Generating Triad Notarizer Approval Vector...")
    tip_nonce = hashlib.sha256(payload_bytes).hexdigest()
    keys_dir = Path("workspace/notary_keys")
    keys_dir.mkdir(parents=True, exist_ok=True)

    if not (keys_dir / "notary_signer_0.key").exists():
        run_cmd([
            sys.executable,
            "notarizer_signer.py",
            "--gen-keys",
            "--keys-dir", str(keys_dir)
        ])

    notary_out = run_cmd([
        sys.executable,
        "notarizer_signer.py",
        "--keys-dir", str(keys_dir),
        "--seq-id", str(seq_id),
        "--nonce-hex", tip_nonce,
        "--out-bin", "workspace/harness_approval.bin"
    ])
    print(notary_out.strip())

    print("\n[3/3] Verifying Dataport Layout Binary Size...")
    approval_bin = Path("workspace/harness_approval.bin")
    if not approval_bin.exists():
        print(f"[-] Error: {approval_bin} was not created", file=sys.stderr)
        return 1

    size = approval_bin.stat().st_size
    if size != 424:
        print(f"[-] Error: expected 424 bytes, got {size}", file=sys.stderr)
        return 1

    print(f"Validation successful: Approval vector is {size} bytes (Seq: {seq_id}), linked to tip {tip_nonce[:16]}...")
    return 0

if __name__ == "__main__":
    sys.exit(main())
