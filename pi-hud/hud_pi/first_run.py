from __future__ import annotations

from typing import Any, Mapping

from .diagnostics import DiagnosticResult, layout_summary, probe_can, probe_display, probe_obd, probe_obd_ble
from .first_run_config import (
    bridge_status,
    can_status,
    default_report_path,
    env_int,
    env_truthy,
    next_steps,
    obd_status,
)
from .first_run_probes import (
    diagnostic_result_dict,
    display_probe_status as _display_probe_status,
    probe_input_status as _probe_input_status,
)


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
    return _probe_input_status(
        obd,
        can,
        enabled,
        obd_timeout,
        can_timeout,
        probe_obd_func=probe_obd,
        probe_obd_ble_func=probe_obd_ble,
        probe_can_func=probe_can,
    )


def display_probe_status(width: int, height: int, enabled: bool) -> dict[str, Any]:
    return _display_probe_status(width, height, enabled, probe_display_func=probe_display)
