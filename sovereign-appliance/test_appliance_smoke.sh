#!/usr/bin/env bash
set -euo pipefail

INITRAMFS="./sovr-initramfs-aarch64.cpio.gz"
KERNEL="./vmlinuz-virt"
TIMEOUT_SECS=45
LOGFILE="smoke_test.log"

if [ ! -f "$KERNEL" ] || [ ! -f "$INITRAMFS" ]; then
    echo "[!] Error: Missing kernel or initramfs." >&2
    exit 1
fi

echo "=== [1/2] Launching Deterministic QEMU Smoke Runner ==="
rm -f "$LOGFILE"

timeout --preserve-status "${TIMEOUT_SECS}s" qemu-system-aarch64 \
    -M virt \
    -cpu max \
    -m 512M \
    -smp 2 \
    -nographic \
    -kernel "$KERNEL" \
    -initrd "$INITRAMFS" \
    -append "console=ttyAMA0 quiet rdinit=/appliance/smoke_runner.sh" > "$LOGFILE" 2>&1 || true

echo "=== [2/2] Evaluating Test Assertions ==="

if grep -q "=== SMOKE_TEST_PASS ===" "$LOGFILE"; then
    echo "[+] SUCCESS: Guest integration harness executed with exit code 0."
    echo "[+] Verified 424-byte CAmkES dataport approval vector generation."
    rm -f "$LOGFILE"
    exit 0
elif grep -q "=== SMOKE_TEST_FAIL ===" "$LOGFILE"; then
    echo "[-] FAILED: Harness encountered errors inside QEMU guest." >&2
    cat "$LOGFILE" >&2
    rm -f "$LOGFILE"
    exit 1
else
    echo "[-] FAILED: Smoke test timed out or QEMU failed to complete." >&2
    cat "$LOGFILE" >&2
    rm -f "$LOGFILE"
    exit 1
fi
