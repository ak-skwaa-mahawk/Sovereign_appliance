#!/usr/bin/env python3
"""
Guest UIO Transport Layer:
Memory-maps the 4KB CAmkES shared dataport at 0x48000000 and interfaces
with the Linux UIO subsystem (/dev/uio0) to trigger and await seL4 doorbells.
"""

import os
import mmap
import struct
import select
from typing import Optional, Tuple

SOVP_OFFSET_PROPOSAL = 0x0000
SOVP_OFFSET_APPROVAL = 0x0400
SOVP_OFFSET_VERDICT  = 0x0600
SOVP_OFFSET_RESULT   = 0x0800
PAGE_SIZE            = 4096

class SovereignGateUIO:
    def __init__(self, uio_device: str = "/dev/uio0"):
        self.uio_device = uio_device
        self.fd: Optional[int] = None
        self.mem: Optional[mmap.mmap] = None
        self._is_mock = False

        if os.path.exists(self.uio_device):
            self.fd = os.open(self.uio_device, os.O_RDWR | os.O_SYNC)
            self.mem = mmap.mmap(
                self.fd,
                PAGE_SIZE,
                mmap.MAP_SHARED,
                mmap.PROT_READ | mmap.PROT_WRITE,
                offset=0
            )
        else:
            # Emulated buffer fallback for environments without native UIO hardware
            self._is_mock = True
            self.mem = mmap.mmap(-1, PAGE_SIZE, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE)

    def write_proposal(self, frame_1024: bytes) -> None:
        if len(frame_1024) != 1024:
            raise ValueError(f"Proposal must be 1024 bytes, got {len(frame_1024)}")
        self.mem.seek(SOVP_OFFSET_PROPOSAL)
        self.mem.write(frame_1024)
        self.mem.flush()

    def write_approval(self, frame_440: bytes) -> None:
        if len(frame_440) != 440:
            raise ValueError(f"Approval must be 440 bytes, got {len(frame_440)}")
        self.mem.seek(SOVP_OFFSET_APPROVAL)
        self.mem.write(frame_440)
        self.mem.flush()

    def read_verdict(self) -> bytes:
        self.mem.seek(SOVP_OFFSET_VERDICT)
        return self.mem.read(96)

    def read_result(self) -> bytes:
        self.mem.seek(SOVP_OFFSET_RESULT)
        return self.mem.read(1024)

    def ring_doorbell(self) -> None:
        """Trigger proposal_ready notification into seL4."""
        if not self._is_mock and self.fd is not None:
            # UIO convention: 4-byte write acknowledges/triggers interrupt
            os.write(self.fd, struct.pack("<I", 1))

    def wait_for_verdict(self, timeout_sec: float = 2.0) -> bool:
        """Await verdict_ready IRQ via GIC SPI notification."""
        if self._is_mock or self.fd is None:
            return True

        r, _, _ = select.select([self.fd], [], [], timeout_sec)
        if r:
            os.read(self.fd, 4) # Consume interrupt event counter
            return True
        return False

    def close(self) -> None:
        if self.mem:
            self.mem.close()
        if self.fd is not None:
            os.close(self.fd)

if __name__ == "__main__":
    gate = SovereignGateUIO()
    print(f"[+] Sovereign UIO Transport initialized (Mode: {'Mock' if gate._is_mock else 'Hardware /dev/uio0'})")
    gate.close()
