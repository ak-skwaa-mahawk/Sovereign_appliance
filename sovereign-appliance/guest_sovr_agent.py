#!/usr/bin/env python3
"""
Sovereign LLM Agent Adapter:
Binds hosted LLM function calls (Grok / Claude / OpenAI) to binary SOVP
proposals for native seL4 admission-gate evaluation.
"""

import os
import sys
import json
import struct
import hashlib
import urllib.request

SOVP_MAGIC        = 0x534F5650
SOVP_VERSION      = 1
TOOL_READ_FILE    = 0x0001
TOOL_HTTP_GET     = 0x0002
TOOL_WRITE_FILE   = 0x0101
TOOL_SEND_MESSAGE = 0x0102

TOOL_NAME_TO_ID = {
    "read_file": TOOL_READ_FILE,
    "http_get": TOOL_HTTP_GET,
    "write_file": TOOL_WRITE_FILE,
    "send_message": TOOL_SEND_MESSAGE,
}

def pack_proposal(tool_id: int, sequence_id: int, session_id: int, payload: bytes) -> bytes:
    if len(payload) > 992:
        raise ValueError(f"Payload exceeds SOVP_MAX_ARGS (992 bytes): {len(payload)}")

    arg_len = len(payload)
    padded_args = payload.ljust(992, b'\x00')

    # Wire format (1024 bytes):
    # uint32 magic (0x00)
    # uint16 version (0x04)
    # uint16 tool_id (0x06)
    # uint64 sequence_id (0x08)
    # uint64 session_id (0x10)
    # uint16 arg_len (0x18)
    # uint16 reserved0 (0x1A)
    # uint32 reserved1 (0x1C)
    # uint8[992] args (0x20)
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

def call_hosted_model(api_key: str, prompt: str, endpoint: str = "https://api.x.ai/v1/chat/completions", model: str = "grok-beta") -> dict:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    tools = [
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Request persistent write to block storage",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"}
                    },
                    "required": ["path", "content"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Request reading a file from storage",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"}
                    },
                    "required": ["path"]
                }
            }
        }
    ]

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "tools": tools,
        "tool_choice": "auto"
    }

    req = urllib.request.Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

if __name__ == "__main__":
    # Test pack proposal output
    test_payload = b"/data/canary.txt\x00Target status check"
    frame = pack_proposal(
        tool_id=TOOL_WRITE_FILE,
        sequence_id=1,
        session_id=0xCAFEBABEDEADBEEF,
        payload=test_payload
    )
    print(f"[+] Local SOVP frame verified: {len(frame)} bytes, SHA256: {hashlib.sha256(frame).hexdigest()[:16]}...")
