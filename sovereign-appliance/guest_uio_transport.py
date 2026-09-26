#!/usr/bin/env python3
"""
Guest UIO Transport Layer:
Memory-maps the 4KB CAmkES shared dataport at 0x48000000 and interfaces
with the Linux UIO subsystem (/dev/uio0) to trigger and await seL4 doorbells.
Provides seamless C-gate in-memory emulation when running in non-seL4 environments.
"""

import os
import mmap
import struct
import select
import ctypes
from typing import Optional

SOVP_OFFSET_PROPOSAL = 0x0000
SOVP_OFFSET_APPROVAL = 0x0400
SOVP_OFFSET_VERDICT  = 0x0600
SOVP_OFFSET_RESULT   = 0x0800
PAGE_SIZE            = 4096

SOVP_MAGIC = 0x534F5650
SOVV_MAGIC = 0x534F5656
SOVQ_MAGIC = 0x534F5651
SOVX_MAGIC = 0x534F5658

DECISION_DENY  = 0
DECISION_ALLOW = 1

SOVR_STATUS_OK = 0x0000

class SovereignGateUIO:
    def __init__(self, uio_device: str = "/dev/uio0", lib_path: str = "./libtoolgate.so"):
        self.uio_device = uio_device
        self.fd: Optional[int] = None
        self.mem: Optional[mmap.mmap] = None
        self._is_mock = False
        self._lib = None

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
            self._is_mock = True
            self.mem = mmap.mmap(-1, PAGE_SIZE, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE)
            if os.path.exists(lib_path):
                self._lib = ctypes.CDLL(os.path.abspath(lib_path))
                self._lib.toolgate_init()

    def write_proposal(self, frame_1024: bytes) -> None:
        if len(frame_1024) != 1024:
            raise ValueError(f"Proposal must be 1024 bytes, got {len(frame_1024)}")
        # Invalidate any stale approval frame
        self.mem.seek(SOVP_OFFSET_APPROVAL)
        self.mem.write(b'\x00' * 4)
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
        """Trigger proposal_ready notification into seL4 or dispatch local C gate."""
        if not self._is_mock and self.fd is not None:
            os.write(self.fd, struct.pack("<I", 1))
        elif self._is_mock and self._lib:
            # Check approval slot first, mirroring toolgate_component.c
            self.mem.seek(SOVP_OFFSET_APPROVAL)
            app_magic = struct.unpack("<I", self.mem.read(4))[0]

            buf_addr = ctypes.c_char_p.from_buffer(self.mem)

            if app_magic == SOVQ_MAGIC:
                app_ptr = ctypes.cast(ctypes.byref(buf_addr, SOVP_OFFSET_APPROVAL), ctypes.c_void_p)
                status = self._lib.toolgate_verify_approval(app_ptr)

                # Write final verdict and simulated execution result
                verdict_frame = struct.pack(
                    "<IHBBQ16s64s",
                    SOVV_MAGIC,
                    status,
                    DECISION_ALLOW if status == SOVR_STATUS_OK else DECISION_DENY,
                    0,
                    0,
                    b'\x00' * 16,
                    b'\x00' * 64
                )
                self.mem.seek(SOVP_OFFSET_VERDICT)
                self.mem.write(verdict_frame)

                if status == SOVR_STATUS_OK:
                    res_msg = b"EXEC_WRITE_OK\n"
                    res_frame = struct.pack(
                        "<IHHQ",
                        SOVX_MAGIC,
                        SOVR_STATUS_OK,
                        len(res_msg),
                        0
                    ) + res_msg.ljust(1008, b'\x00')
                    self.mem.seek(SOVP_OFFSET_RESULT)
                    self.mem.write(res_frame)

                # Invalidate approval magic after consumption
                self.mem.seek(SOVP_OFFSET_APPROVAL)
                self.mem.write(b'\x00' * 4)
            else:
                prop_ptr = ctypes.cast(ctypes.byref(buf_addr, SOVP_OFFSET_PROPOSAL), ctypes.c_void_p)
                verdict_ptr = ctypes.cast(ctypes.byref(buf_addr, SOVP_OFFSET_VERDICT), ctypes.c_void_p)
                self._lib.toolgate_handle_proposal(prop_ptr, verdict_ptr)

                # Direct execution result emulation for ALLOWed operations
                self.mem.seek(SOVP_OFFSET_VERDICT)
                v_magic, v_status, v_decision = struct.unpack("<IHB", self.mem.read(7))
                if v_decision == DECISION_ALLOW and v_status == SOVR_STATUS_OK:
                    res_msg = b"EXEC_READ_OK\n"
                    res_frame = struct.pack(
                        "<IHHQ",
                        SOVX_MAGIC,
                        SOVR_STATUS_OK,
                        len(res_msg),
                        0
                    ) + res_msg.ljust(1008, b'\x00')
                    self.mem.seek(SOVP_OFFSET_RESULT)
                    self.mem.write(res_frame)

    def wait_for_verdict(self, timeout_sec: float = 2.0) -> bool:
        if self._is_mock or self.fd is None:
            return True
        r, _, _ = select.select([self.fd], [], [], timeout_sec)
        if r:
            os.read(self.fd, 4)
            return True
        return False

    def close(self) -> None:
        if self.mem:
            self.mem.close()
        if self.fd is not None:
            os.close(self.fd)
