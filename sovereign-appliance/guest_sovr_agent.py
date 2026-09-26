#!/usr/bin/env python3
"""
Sovereign LLM Agent Adapter:
Binds hosted LLM function calls (Grok / Claude / OpenAI) to binary SOVP
proposals and writes them to the seL4 admission-gate via UIO dataport.
"""

import os
import sys
import json
import struct
import hashlib
import urllib.request
from guest_uio_transport import SovereignGateUIO

SOVP_MAGIC        = 0x534F5650
SOVV_MAGIC        = 0x534F5656
SOVP_VERSION      = 1
TOOL_READ_FILE    = 0x0001
TOOL_HTTP_GET     = 0x0002
TOOL_WRITE_FILE   = 0x0101
TOOL_SEND_MESSAGE = 0x0102

DECISION_DENY     = 0
DECISION_ALLOW    = 1
DECISION_QUORUM   = 2

def pack_proposal(tool_id: int, sequence_id: int, session_id: int, payload: bytes) -> bytes:
    if len(payload) > 992:
        raise ValueError(f"Payload exceeds SOVP_MAX_ARGS (992 bytes): {len(payload)}")

    arg_len = len(payload)
    padded_args = payload.ljust(992, b'\x00')

    header = struct.pack(
        "<IIQQHH I",
        SOVP_MAGIC,
        (SOVP_VERSION) | (tool_id << 16),
        sequence_id,
        session_id,
        arg_len,
        0,
        0
    )
    frame = header + padded_args
    assert len(frame) == 1024, f"Frame must be exactly 1024 bytes, got {len(frame)}"
    return frame

def submit_proposal(transport: SovereignGateUIO, tool_id: int, seq: int, session: int, payload: bytes) -> dict:
    frame = pack_proposal(tool_id, seq, session, payload)
    transport.write_proposal(frame)
    transport.ring_doorbell()

    if not transport.wait_for_verdict(timeout_sec=2.0):
        return {"status": "TIMEOUT", "decision": DECISION_DENY}

    raw_verdict = transport.read_verdict()
    magic, status, decision, req_mask, ret_seq = struct.unpack("<IHBBQ", raw_verdict[:16])

    return {
        "magic": hex(magic),
        "status_code": hex(status),
        "decision": decision,
        "required_mask": hex(req_mask),
        "sequence_id": ret_seq,
        "challenge": raw_verdict[32:96]
    }

if __name__ == "__main__":
    gate = SovereignGateUIO()
    test_payload = b"/data/canary.txt\x00Verification"
    print(f"[+] Submitting sample tool proposal to gate via UIO...")
    res = submit_proposal(gate, TOOL_WRITE_FILE, 1, 0x1337CAFE, test_payload)
    print(f"[+] Gate response: {res}")
    gate.close()
