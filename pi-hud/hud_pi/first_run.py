from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .diagnostics import DiagnosticResult, layout_summary, probe_can, probe_display, probe_obd, probe_obd_ble


def env_truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def env_int(environ: Mapping[str, str], key: str, fallback: int) -> int:
    try:
        return int(str(environ.get(key, fallback)).strip())
    except (TypeError, ValueError):
        return fallback


def build_first_run_report(
    environ: Mapping[str, str],
    probe_inputs: bool = False,
    obd_timeout: float = 2.0,
    can_timeout: float = 3.0,
    probe_display_output: bool = False,
) -> dict[str, Any]:
    layout_path = environ.get("HEADUNIT_HUD_LAYOUT", "layouts/avante_hd_2010_default.json")
    width = env_int(environ, "HEADUNIT_HUD_WIDTH", 1920)
    height = env_int(environ, "HEADUNIT_HUD_HEIGHT", 480)
    dummy_enabled = env_truthy(environ.get("HEADUNIT_HUD_DUMMY", "0"))
    require_handoff = env_truthy(environ.get("HEADUNIT_HUD_REQUIRE_HANDOFF", "0"))

    layout_result = layout_summary(layout_path, width=width, height=height, require_handoff=require_handoff)
    obd = obd_status(environ)
    can = can_status(environ)
    bridge = bridge_status(environ)

    blocking_issues: list[str] = []
    if not layout_result.ok:
        blocking_issues.append(f"layout is not valid: {layout_result.detail}")
    if width != 1920 or height != 480:
        blocking_issues.append(f"display size is {width}x{height}, expected 1920x480")
    if dummy_enabled:
        blocking_issues.append("dummy mode is enabled")
    if not obd["configured"]:
        blocking_issues.append(obd["issue"])
    if not can["configured"]:
        blocking_issues.append(can["issue"])
    input_probes = probe_input_status(obd, can, enabled=probe_inputs, obd_timeout=obd_timeout, can_timeout=can_timeout)
    display_probe = display_probe_status(width, height, enabled=probe_display_output)
    input_probe_issues = input_probes["issues"]
    display_probe_issues = display_probe["issues"]
    probe_issues = input_probe_issues + display_probe_issues

    return {
        "schema_version": 1,
        "standalone_ready": not blocking_issues,
        "live_input_ready": bool(probe_inputs and not input_probe_issues),
        "display_ready": bool(probe_display_output and not display_probe_issues),
        "blocking_issues": blocking_issues,
        "probe_issues": probe_issues,
        "layout": {
            "path": str(layout_path),
            "ok": layout_result.ok,
            "detail": layout_result.detail,
            "require_handoff": require_handoff,
        },
        "display": {
            "width": width,
            "height": height,
            "expected": [1920, 480],
            "ok": width == 1920 and height == 480,
            "probe": display_probe,
        },
        "dummy_enabled": dummy_enabled,
        "obd": obd,
        "can": can,
        "input_probes": input_probes,
        "android_bridge": bridge,
        "next_steps": next_steps(
            obd,
            can,
            dummy_enabled,
            probe_inputs=probe_inputs,
            input_probe_issues=input_probe_issues,
            probe_display_output=probe_display_output,
            display_probe_issues=display_probe_issues,
        ),
    }


def probe_input_status(obd: dict[str, Any], can: dict[str, Any], enabled: bool, obd_timeout: float, can_timeout: float) -> dict[str, Any]:
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
            obd_result = probe_obd(str(obd.get("port", "")), int(obd.get("baud", 38400)), obd_timeout)
        elif obd.get("transport") == "ble":
            obd_result = probe_obd_ble(str(obd.get("mac", "")), str(obd.get("rx_uuid", "")), str(obd.get("tx_uuid", "")), obd_timeout)
        else:
            obd_result = DiagnosticResult("obd", False, "unsupported OBD transport")
    else:
        obd_result = DiagnosticResult("obd", False, obd.get("issue", "OBD is not configured"))
    result["obd"] = diagnostic_result_dict(obd_result)
    if not obd_result.ok:
        result["issues"].append(f"OBD live probe failed: {obd_result.detail}")

    if can.get("configured"):
        can_result = probe_can(str(can.get("channel", "")), can_timeout)
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


def display_probe_status(width: int, height: int, enabled: bool) -> dict[str, Any]:
    result: dict[str, Any] = {
        "enabled": enabled,
        "ok": None,
        "name": "",
        "detail": "not run",
        "issues": [],
    }
    if not enabled:
        return result

    probe_result = probe_display(width, height)
    result.update(diagnostic_result_dict(probe_result))
    if not probe_result.ok:
        result["issues"].append(f"display probe failed: {probe_result.detail}")
    return result


def obd_status(environ: Mapping[str, str]) -> dict[str, Any]:
    port = environ.get("HEADUNIT_HUD_OBD_PORT", "").strip()
    baud = env_int(environ, "HEADUNIT_HUD_OBD_BAUD", 38400)
    ble_mac = environ.get("HEADUNIT_HUD_OBD_BLE_MAC", "").strip()
    ble_rx_uuid = environ.get("HEADUNIT_HUD_OBD_BLE_RX_UUID", "").strip()
    ble_tx_uuid = environ.get("HEADUNIT_HUD_OBD_BLE_TX_UUID", "").strip()

    if port:
        return {
            "configured": True,
            "transport": "serial",
            "port": port,
            "baud": baud,
            "issue": "",
        }
    if ble_mac:
        configured = bool(ble_rx_uuid and ble_tx_uuid)
        return {
            "configured": configured,
            "transport": "ble",
            "mac": ble_mac,
            "rx_uuid": ble_rx_uuid,
            "tx_uuid": ble_tx_uuid,
            "issue": "" if configured else "OBD BLE RX/TX UUID is missing",
        }
    return {
        "configured": False,
        "transport": "not-configured",
        "issue": "OBD/iCar input is not configured",
    }


def can_status(environ: Mapping[str, str]) -> dict[str, Any]:
    channel = environ.get("HEADUNIT_HUD_CAN_CHANNEL", "").strip()
    bitrate = env_int(environ, "HEADUNIT_HUD_CAN_BITRATE", 500000)
    listen_only = environ.get("HEADUNIT_HUD_CAN_LISTEN_ONLY", "on").strip() or "on"
    return {
        "configured": bool(channel),
        "channel": channel,
        "bitrate": bitrate,
        "listen_only": listen_only,
        "issue": "" if channel else "CANable SocketCAN channel is not configured",
    }


def bridge_status(environ: Mapping[str, str]) -> dict[str, Any]:
    return {
        "role": "navigation_and_backup_speed_only",
        "required_for_standalone": False,
        "udp_port": env_int(environ, "HEADUNIT_HUD_UDP_PORT", 4210),
        "discovery_port": env_int(environ, "HEADUNIT_HUD_DISCOVERY_PORT", 4211),
        "discovery_enabled": not env_truthy(environ.get("HEADUNIT_HUD_DISABLE_DISCOVERY", "0")),
    }


def next_steps(
    obd: dict[str, Any],
    can: dict[str, Any],
    dummy_enabled: bool,
    probe_inputs: bool = False,
    input_probe_issues: list[str] | None = None,
    probe_display_output: bool = False,
    display_probe_issues: list[str] | None = None,
) -> list[str]:
    steps: list[str] = []
    if dummy_enabled:
        steps.append("Set HEADUNIT_HUD_DUMMY=0 for real Pi standalone use.")
    if not obd["configured"]:
        if obd["transport"] == "ble":
            steps.append("Fill HEADUNIT_HUD_OBD_BLE_RX_UUID and HEADUNIT_HUD_OBD_BLE_TX_UUID, then run diagnose-inputs.py.")
        else:
            steps.append("Set HEADUNIT_HUD_OBD_PORT=/dev/rfcomm0 or configure HEADUNIT_HUD_OBD_BLE_* for iCar Pro 2S.")
    if not can["configured"]:
        steps.append("Set HEADUNIT_HUD_CAN_CHANNEL=can0 and bring CANable up in listen-only mode.")
    if probe_inputs and input_probe_issues:
        steps.append("Fix live OBD/CAN probe failures before relying on real vehicle data.")
    if probe_display_output and display_probe_issues:
        steps.append("Fix the Pi framebuffer/display mode before relying on the 1920x480 HUD.")
    if not steps:
        steps.append("Run diagnose-inputs.py, then collect-vehicle-baseline.py with ignition on.")
    return steps


def default_report_path(app_dir: str | Path = "/opt/headunit-pi-hud") -> Path:
    return Path(app_dir) / "vehicle-baseline" / "first-run-status.json"
