from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .diagnostics import DiagnosticResult, probe_can, probe_display, probe_obd, probe_obd_ble


ProbeObdFunc = Callable[[str, int, float], DiagnosticResult]
ProbeObdBleFunc = Callable[[str, str, str, float], DiagnosticResult]
ProbeCanFunc = Callable[[str, float], DiagnosticResult]
ProbeDisplayFunc = Callable[[int, int], DiagnosticResult]


def probe_input_status(
    obd: dict[str, Any],
    can: dict[str, Any],
    enabled: bool,
    obd_timeout: float,
    can_timeout: float,
    *,
    probe_obd_func: ProbeObdFunc = probe_obd,
    probe_obd_ble_func: ProbeObdBleFunc = probe_obd_ble,
    probe_can_func: ProbeCanFunc = probe_can,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "enabled": enabled,
        "obd": {"ok": None, "name": "", "detail": "not run"},
        "can": {"ok": None, "name": "", "detail": "not run"},
        "issues": [],
    }
    if not enabled:
        return result

    if obd.get("configured"):
        if obd.get("transport") == "serial":
            obd_result = probe_obd_func(str(obd.get("port", "")), int(obd.get("baud", 38400)), obd_timeout)
        elif obd.get("transport") == "ble":
            obd_result = probe_obd_ble_func(str(obd.get("mac", "")), str(obd.get("rx_uuid", "")), str(obd.get("tx_uuid", "")), obd_timeout)
        else:
            obd_result = DiagnosticResult("obd", False, "unsupported OBD transport")
    else:
        obd_result = DiagnosticResult("obd", False, obd.get("issue", "OBD is not configured"))
    result["obd"] = diagnostic_result_dict(obd_result)
    if not obd_result.ok:
        result["issues"].append(f"OBD live probe failed: {obd_result.detail}")

    if can.get("configured"):
        can_result = probe_can_func(str(can.get("channel", "")), can_timeout)
    else:
        can_result = DiagnosticResult("can", False, can.get("issue", "CAN is not configured"))
    result["can"] = diagnostic_result_dict(can_result)
    if not can_result.ok:
        result["issues"].append(f"CAN live probe failed: {can_result.detail}")

    return result


def diagnostic_result_dict(result: DiagnosticResult) -> dict[str, Any]:
    return {
        "name": result.name,
        "ok": result.ok,
        "detail": result.detail,
    }


def display_probe_status(
    width: int,
    height: int,
    enabled: bool,
    *,
    probe_display_func: ProbeDisplayFunc = probe_display,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "enabled": enabled,
        "ok": None,
        "name": "",
        "detail": "not run",
        "issues": [],
    }
    if not enabled:
        return result

    probe_result = probe_display_func(width, height)
    result.update(diagnostic_result_dict(probe_result))
    if not probe_result.ok:
        result["issues"].append(f"display probe failed: {probe_result.detail}")
    return result
