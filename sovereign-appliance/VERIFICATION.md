# Sovereign seL4 Appliance Admission Gate: Verification & Specification Guide

This document details the deterministic build pipeline, hardware-isolated dataport memory layout, and end-to-end handshake verification procedure for the Sovereign Appliance Admission Gate (`Soliton-north-star-node` / `admission-gate`).

---

## 1. System Overview & Dual-Remote Architecture

The sovereign admission gate implements a capability-gated execution envelope across two cooperating operational roles:

* **Ingress Node (`firecrawl_ingress.py`)**: Sanitizes incoming crawling/index payloads, stages them to `/appliance/workspace/firecrawl_data`, and generates deterministic proposal transactions conforming to `admission_gate.toml`.
* **Quorum Signer (`notarizer_signer.py`)**: Implements an offline Ed25519 Triad witness signing service (mask `0x07` = Signers 0, 1, 2) that cryptographically signs the latest audit log tip / challenge nonce and writes a 424-byte binary approval block directly to the shared CAmkES dataport memory region.
* **Dual-Push Upstream Sync**: The repository continuously synchronizes across two remote endpoints:
  - `https://github.com/ak-skwaa-mahawk/Soliton-north-star-node.git`
  - `https://github.com/ak-skwaa-mahawk/admission-gate.git`

---

## 2. Shared Memory Dataport Specification (CAmkES 4 KB Frame)

The sovereign runtime utilizes a 4096-byte memory-mapped dataport page shared between the untrusted agent userland and the seL4 admission-gate monitor.

+-----------------------------------------------------------------------+
| Offset Range   | Size      | Component / Structure                    |
+-----------------------------------------------------------------------+
| 0x0000 - 0x03FF| 1024 B    | Proposal Payload Block (JSON-RPC Wire)   |
| 0x0400 - 0x05A7|  424 B    | Quorum Approval Vector (struct approval) |
| 0x05A8 - 0x05FF|   88 B    | Reserved / Alignment Padding             |
| 0x0600 - 0x07FF|  512 B    | Gate Execution Verdict & Nonce Record    |
| 0x0800 - 0x0FFF| 2048 B    | Ring Buffer / Cryptographic Audit Trail  |
+-----------------------------------------------------------------------+

### 2.1 C Struct Definition (`offset 0x0400`)

```c
#include <stdint.h>

struct __attribute__((__packed__)) gate_approval {
    uint32_t seq_id;              /* +0x00: Monotonic Proposal Sequence ID          */
    uint8_t  witness_mask;         /* +0x04: Bitmask of signers (0x07 = Triad 0,1,2) */
    uint8_t  reserved[3];          /* +0x05: Canonical zero-padding                  */
    uint8_t  challenge_nonce[32];  /* +0x08: 32-byte hash matching audit entry tip   */
    uint8_t  signatures[6][64];    /* +0x28: Up to 6 x 64-byte Ed25519 signatures    */
};

_Static_assert(sizeof(struct gate_approval) == 424, "gate_approval struct must be exactly 424 bytes");
3. Deterministic Build Pipeline
​The root filesystem is provisioned via build.sh using an Alpine Linux aarch64 minimal baseline inside a PRoot containment wrapper.
​Build Stages:
​Fetch Baseline: Pulls official Alpine v3.24 minimal rootfs archive (alpine-minirootfs-3.24.0-aarch64.tar.gz).
​Unpack Rootfs Tree: Sets up pseudofs mounts and sets DNS to 1.1.1.1.
​Provisioning Packages:
​python3 (v3.14+)
​py3-cryptography (Ed25519 primitives)
​coreutils
​admission-gate (installed from local source via --break-system-packages)
​Appliance Staging: Installs /init, stage binaries (firecrawl_ingress.py, notarizer_signer.py, test_handshake_harness.py), and sets standard /usr/bin environment paths in admission_gate.toml.
​Deterministic Artifact Packaging:
​Compresses tarball: sovr-rootfs-aarch64.tar.gz + SHA256 manifest.
​Generates bootable CPIO archive: sovr-initramfs-aarch64.cpio.gz + SHA256 manifest.
​Executing the Build:
bash
cd ~/sovereign-appliance
./build.sh
4. End-to-End Handshake Verification Procedure
​4.1 Running via QEMU AArch64 Appliance
​Launch the guest virtual machine:
badh
./run-sovr-appliance.sh
Inside the booted appliance shell (/bin/sh):
sh
cd /appliance
./test_handshake_harness.py

4.2 Expected Verification Log
text
[1/3] Testing Firecrawl Ingress & Gate Policy...
[Agent Gate] Online (Active Gate). Log: audit_log.jsonl (Tip: 0000000000000000...)
Result [crawl_harness_run_01_...]: Code 0 - 7775aeeea262e831...  /appliance/workspace/firecrawl_data/harness_run_01_7775aeeea262e831.json
[Ingress] Artifact persisted: /appliance/workspace/firecrawl_data/harness_run_01_7775aeeea262e831.json
[Ingress] Proposal payload: {"action_id": "...", "origin": "firecrawl", "command": "sha256sum ...", "target_path": "/appliance/workspace/firecrawl_data", "risk_tier": 1}

[2/3] Generating Triad Notarizer Approval Vector...
[Notarizer] Approval block written to workspace/harness_approval.bin (424 bytes)

[3/3] Verifying Dataport Layout Binary Size...
Validation successful: Approval vector is 424 bytes, linked to tip ...
4.3 Verifying Persistent Audit Trail
​Confirm that the hash chain is intact:
sh
tail -n 1 /appliance/audit_log.jsonl
Key fields to check:
​"env_scrubbed": true
​"policy_passed": true
​"entry_hash" matches the 32-byte nonce used in the notarizer approval vector.
​4.4 Graceful Shutdown
sh
poweroff -f
5. Security & Isolation Invariants
​Path Traversal Protection: Any command targeting directories outside /appliance/workspace or declared in admission_gate.toml is rejected with Blocked.
​Command Whitelisting: Binaries such as rm, dd, chmod, and chown trigger immediate denial before spawning subprocesses.
​Quorum Strictness: The CAmkES dataport monitor rejects approval payloads if fewer than 3 valid Ed25519 signatures are populated under the 0x07 bitmask.

---

## 6. Automated Headless Verification & CAmkES Reader

### 6.1 Running the Non-Interactive QEMU Smoke Test

The automated runner executes the full ingress, policy check, and quorum signing sequence in a headless QEMU instance via the `smoke` kernel parameter, evaluating pass/fail status and powering off automatically:

```bash
./test_appliance_smoke.sh
Expected terminal output:
text
=== [1/2] Launching Deterministic QEMU Smoke Runner ===
=== [2/2] Evaluating Test Assertions ===
[+] SUCCESS: Guest integration harness executed with exit code 0.
[+] Verified 424-byte CAmkES dataport approval vector generation.

6.2 Inspecting the Dataport Approval Binary
​Use gate_dataport_reader to parse and assert the 424-byte struct layout directly from the filesystem or memory-mapped dataport buffer:
bash
clang -Wall -Wextra -O2 gate_dataport_reader.c -o gate_dataport_reader
./gate_dataport_reader ./workspace/harness_approval.bin

Expected output:

text
=== CAmkES Dataport Approval Inspection (Offset 0x0400) ===
  Sequence ID  : 42
  Witness Mask : 0x07
  Quorum Status: Verified (Triad quorum 0x07 satisfied)
  Challenge Nonce (32B): <32-byte hex tip>
  Signature [0] : Valid (64 bytes populated)
  Signature [1] : Valid (64 bytes populated)
  Signature [2] : Valid (64 bytes populated)
  Total Populated Signatures: 3
[+] CAmkES dataport approval vector layout is structurally valid.

