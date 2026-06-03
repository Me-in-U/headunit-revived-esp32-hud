from __future__ import annotations

import time
from typing import Any

from .diagnostics_common import DiagnosticResult


def open_socketcan_bus(can_module: Any, channel: str) -> Any:
    try:
        return can_module.interface.Bus(channel=channel, interface="socketcan")
    except TypeError:
        return can_module.interface.Bus(channel=channel, bustype="socketcan")


def probe_can(channel: str, timeout: float = 3.0) -> DiagnosticResult:
    try:
        import can
    except ImportError:
        return DiagnosticResult("can", False, "python-can is not installed")

    try:
        bus = open_socketcan_bus(can, channel)
    except Exception as exc:
        return DiagnosticResult("can", False, f"{channel} open error: {exc.__class__.__name__}")

    frame_count = 0
    last_id: int | None = None
    deadline = time.monotonic() + timeout
    try:
        while time.monotonic() < deadline:
            remaining = max(0.05, min(0.5, deadline - time.monotonic()))
            message = bus.recv(timeout=remaining)
            if message is None:
                continue
            frame_count += 1
            last_id = int(message.arbitration_id)
    except Exception as exc:
        return DiagnosticResult("can", False, f"{channel} receive error: {exc.__class__.__name__}")
    finally:
        shutdown = getattr(bus, "shutdown", None)
        if callable(shutdown):
            shutdown()

    if frame_count == 0:
        return DiagnosticResult("can", False, f"{channel} opened but no CAN frames within {timeout:.1f}s")
    return DiagnosticResult("can", True, f"{channel} frames={frame_count}, last_id=0x{last_id:X}")
