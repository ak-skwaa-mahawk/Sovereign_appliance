#!/usr/bin/env bash
set -euo pipefail

ROOTFS_DIR="$(pwd)/rootfs_tree"
OUTPUT_TAR="sovr-rootfs-aarch64.tar.gz"
DOWNLOAD_URL="https://dl-cdn.alpinelinux.org/alpine/latest-stable/releases/aarch64/alpine-minirootfs-3.24.0-aarch64.tar.gz"

if [ ! -d "${ROOTFS_DIR}/bin" ]; then
    echo "=== [1/4] Fetching verified baseline (~3.8 MB) ==="
    curl -f -L "${DOWNLOAD_URL}" -o miniroot.tar.gz
    echo "=== [2/4] Unpacking baseline into tree ==="
    gzip -t miniroot.tar.gz
    tar -xzf miniroot.tar.gz -C "${ROOTFS_DIR}"
    rm -f miniroot.tar.gz
fi

echo "=== [3/4] Configuring DNS & Installing declarative package set ==="
mkdir -p "${ROOTFS_DIR}/etc" "${ROOTFS_DIR}/tmp"
echo "nameserver 1.1.1.1" > "${ROOTFS_DIR}/etc/resolv.conf"

cp packages.list "${ROOTFS_DIR}/tmp/"
cp configure-system.sh "${ROOTFS_DIR}/tmp/"

# Unset LD_PRELOAD to disable termux-exec wrapper interception
unset LD_PRELOAD

proot \
  -0 \
  -r "${ROOTFS_DIR}" \
  -w / \
  --link2symlink \
  -b /dev \
  -b /proc \
  -b /sys \
  /bin/sh -c '
    export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
    apk update
    apk add --no-cache $(cat /tmp/packages.list)
    /bin/sh /tmp/configure-system.sh
    rm -f /tmp/packages.list /tmp/configure-system.sh
'

echo "=== [4/4] Packing deterministic rootfs image ==="
tar -czf "${OUTPUT_TAR}" -C "${ROOTFS_DIR}" .
sha256sum "${OUTPUT_TAR}" > "${OUTPUT_TAR}.sha256"

# Cleanup unpacked tree to conserve internal storage
rm -rf "${ROOTFS_DIR}"

echo ""
echo "=========================================================="
echo "[+] Rootfs generated successfully:"
echo "    Archive: $(pwd)/${OUTPUT_TAR}"
echo "    Size:    $(du -h "${OUTPUT_TAR}" | cut -f1)"
echo "    SHA256:  $(cat "${OUTPUT_TAR}.sha256")"
echo "=========================================================="
