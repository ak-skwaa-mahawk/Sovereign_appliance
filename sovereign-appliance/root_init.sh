#!/bin/sh
set -x
mkdir -p /proc /sys /dev /tmp /appliance/workspace
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev
mkdir -p /dev/pts
mount -t devpts devpts /dev/pts
mount -t tmpfs tmpfs /tmp

export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export PYTHONUNBUFFERED=1

echo "=========================================="
echo " Sovereign Appliance Automated Smoke Test"
echo "=========================================="

cd /appliance
if [ -f ./test_handshake_harness.py ]; then
    python3 ./test_handshake_harness.py
    STATUS=$?
    if [ $STATUS -eq 0 ]; then
        if [ -x /appliance/gate_dataport_reader ]; then
            echo "[4/4] Verifying Dataport Vector via In-Guest CAmkES Reader..."
            /appliance/gate_dataport_reader /appliance/workspace/harness_approval.bin /appliance/workspace/notary_keys
            if [ $? -ne 0 ]; then
                echo "[-] In-guest CAmkES verification failed"
                STATUS=1
            fi
        fi
        echo "=== SMOKE_TEST_PASS ==="
    else
        echo "=== SMOKE_TEST_FAIL ==="
    fi
else
    echo "[-] test_handshake_harness.py not found in /appliance"
    echo "=== SMOKE_TEST_FAIL ==="
fi

poweroff -f
reboot -f
