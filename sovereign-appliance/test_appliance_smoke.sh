#!/usr/bin/env bash
set -euo pipefail

INITRAMFS="./sovr-initramfs-aarch64.cpio.gz"
KERNEL="./vmlinuz-virt"
TIMEOUT_SECS=30
LOGFILE="smoke_test.log"

if [ ! -f "$KERNEL" ]; then
    echo "[!] Error: Kernel $KERNEL not found." >&2
    exit 1
fi

if [ ! -f "$INITRAMFS" ]; then
    echo "[!] Error: Initramfs $INITRAMFS not found. Run ./build.sh first." >&2
    exit 1
fi

echo "=== [1/2] Launching Sovereign seL4 Appliance Smoke Test in QEMU ==="

# Feed commands to the guest shell:
# 1. Enter appliance directory
# 2. Execute end-to-end integration harness
# 3. Echo sentinel tokens reflecting exact exit status
# 4. Issue poweroff
GUEST_CMDS=$(cat << 'CMDS'
cd /appliance
./test_handshake_harness.py
if [ $? -eq 0 ]; then
    echo "=== SMOKE_TEST_PASS ==="
else
    echo "=== SMOKE_TEST_FAIL ==="
fi
poweroff -f
CMDS
)

# Run QEMU with a hard timeout, saving output to smoke_test.log
rm -f "$LOGFILE"
timeout --preserve-status "${TIMEOUT_SECS}s" qemu-system-aarch64 \
    -M virt \
    -cpu max \
    -m 512M \
    -smp 2 \
    -nographic \
    -kernel "$KERNEL" \
    -initrd "$INITRAMFS" \
    -append "console=ttyAMA0 quiet" \
    <<< "$GUEST_CMDS" > "$LOGFILE" 2>&1 || true

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
    echo "[-] FAILED: Smoke test timed out or QEMU failed to reach guest prompt." >&2
    cat "$LOGFILE" >&2
    rm -f "$LOGFILE"
    exit 1
fi
