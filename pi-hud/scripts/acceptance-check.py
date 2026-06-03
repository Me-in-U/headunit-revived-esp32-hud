#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping

PI_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = PI_DIR.parent
if str(PI_DIR) not in sys.path:
    sys.path.insert(0, str(PI_DIR))

from hud_pi.diagnostics import DiagnosticResult, load_env_file
from hud_pi.first_run import build_first_run_report
from hud_pi.layout import load_layout
from hud_pi.vehicle_profiles import load_vehicle_profile_entries


def default_env_file_path() -> Path:
    configured = os.environ.get("HEADUNIT_HUD_ENV_FILE", "").strip()
    if configured:
        return Path(configured)
    return Path("/etc/headunit-pi-hud.env")


def default_acceptance_path(app_dir: str | Path = "/opt/headunit-pi-hud") -> Path:
    return Path(app_dir) / "vehicle-baseline" / "acceptance-check.json"


def default_layout_path() -> str:
    return os.environ.get(
        "HEADUNIT_HUD_LAYOUT",
        str(ROOT_DIR / "layouts" / "avante_hd_2010_default.json"),
    )


def env_int(key: str, fallback: int) -> int:
    try:
        return int(str(os.environ.get(key, fallback)).strip())
    except (TypeError, ValueError):
        return fallback


def preparse_env_file(argv: list[str] | None) -> Path:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--env-file", default=str(default_env_file_path()))
    args, _ = parser.parse_known_args(argv)
    return Path(args.env_file)


def load_runtime_environment(env_file: Path) -> list[str]:
    os.environ["HEADUNIT_HUD_ENV_FILE"] = str(env_file)
    return load_env_file(env_file, os.environ)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Raspberry Pi HUD pre-car acceptance check")
    parser.add_argument("--env-file", default=str(default_env_file_path()), help="Runtime environment file")
    parser.add_argument("--layout", default=default_layout_path(), help="Layout JSON path")
    parser.add_argument("--width", type=int, default=env_int("HEADUNIT_HUD_WIDTH", 1920))
    parser.add_argument("--height", type=int, default=env_int("HEADUNIT_HUD_HEIGHT", 480))
    parser.add_argument(
        "--output",
        default=os.environ.get(
            "HEADUNIT_HUD_ACCEPTANCE_OUTPUT",
            str(default_acceptance_path(os.environ.get("HEADUNIT_HUD_APP_DIR", ROOT_DIR))),
        ),
    )
    parser.add_argument("--json", action="store_true", help="Print the full JSON report")
    parser.add_argument("--no-write", action="store_true", help="Do not write the JSON report to --output")
    parser.add_argument("--probe-display", action="store_true", help="Verify the Pi framebuffer size")
    parser.add_argument("--probe-inputs", action="store_true", help="Run live OBD/CAN probes")
    parser.add_argument("--require-handoff", action="store_true", help="Require editor-generated Pi handoff metadata")
    parser.add_argument("--obd-timeout", type=float, default=2.0)
    parser.add_argument("--can-timeout", type=float, default=3.0)
    return parser


def build_acceptance_report(
    environ: Mapping[str, str],
    probe_inputs: bool = False,
    obd_timeout: float = 2.0,
    can_timeout: float = 3.0,
    probe_display_output: bool = False,
) -> dict[str, Any]:
    first_run = build_first_run_report(
        environ,
        probe_inputs=probe_inputs,
        obd_timeout=obd_timeout,
        can_timeout=can_timeout,
        probe_display_output=probe_display_output,
    )
    vehicle_profile = vehicle_profile_status(environ, first_run)
    acceptance = build_acceptance_summary(
        first_run,
        vehicle_profile,
        probe_inputs=probe_inputs,
        probe_display_output=probe_display_output,
    )
    return {
        "schema_version": 1,
        "acceptance": acceptance,
        "vehicle_profile": vehicle_profile,
        "first_run": first_run,
    }


def build_acceptance_summary(
    first_run: Mapping[str, Any],
    vehicle_profile: Mapping[str, Any],
    probe_inputs: bool = False,
    probe_display_output: bool = False,
) -> dict[str, Any]:
    layout_ready = bool(first_run["layout"]["ok"])
    display_ready = bool(first_run["display"]["ok"]) and (not probe_display_output or bool(first_run["display_ready"]))
    standalone_ready = bool(first_run["standalone_ready"])
    bridge_optional = not bool(first_run["android_bridge"].get("required_for_standalone", True))
    pi_vehicle_inputs_configured = bool(first_run["obd"]["configured"] and first_run["can"]["configured"])
    vehicle_profile_ready = bool(vehicle_profile["ok"])
    live_input_ready = bool(first_run["live_input_ready"])

    issues: list[str] = []
    append_unique(issues, first_run["blocking_issues"])
    if not display_ready and not first_run["display"]["ok"]:
        issues.append(f"display size is {first_run['display']['width']}x{first_run['display']['height']}, expected 1920x480")
    if probe_display_output or probe_inputs:
        append_unique(issues, first_run["probe_issues"])
    if not bridge_optional:
        issues.append("Android bridge is marked as required, but Pi HUD must be standalone.")
    if not pi_vehicle_inputs_configured:
        issues.append("Pi vehicle inputs are not fully configured: OBD/iCar and CANable are both required.")
    append_unique(issues, vehicle_profile.get("issues", []))

    ready_for_car = (
        layout_ready
        and display_ready
        and standalone_ready
        and bridge_optional
        and pi_vehicle_inputs_configured
        and vehicle_profile_ready
        and (not probe_inputs or live_input_ready)
    )

    return {
        "ready_for_car": ready_for_car,
        "layout_ready": layout_ready,
        "display_ready": display_ready,
        "standalone_ready": standalone_ready,
        "live_input_ready": live_input_ready,
        "bridge_optional": bridge_optional,
        "pi_vehicle_inputs_configured": pi_vehicle_inputs_configured,
        "vehicle_profile_ready": vehicle_profile_ready,
        "probe_inputs_required": probe_inputs,
        "probe_display_required": probe_display_output,
        "issues": issues,
    }


def vehicle_profile_status(environ: Mapping[str, str], first_run: Mapping[str, Any]) -> dict[str, Any]:
    layout_path = Path(str(first_run["layout"].get("path", "")))
    vehicles_dir = vehicle_profiles_dir(environ)
    result: dict[str, Any] = {
        "ok": False,
        "selected_vehicle": "",
        "vehicles_dir": str(vehicles_dir),
        "path": "",
        "label": "",
        "issues": [],
    }

    if not first_run["layout"].get("ok"):
        result["issues"].append("vehicle profile was not checked because layout is invalid")
        return result

    try:
        layout = load_layout(layout_path)
    except (OSError, json.JSONDecodeError) as error:
        result["issues"].append(f"vehicle profile was not checked because layout could not be loaded: {error}")
        return result

    selected_vehicle = str(layout.get("selected_vehicle", "")).strip()
    result["selected_vehicle"] = selected_vehicle
    if not selected_vehicle:
        result["issues"].append("layout has no selected_vehicle")
        return result
    if not vehicles_dir.is_dir():
        result["issues"].append(f"vehicle profiles dir is missing: {vehicles_dir}")
        return result

    try:
        profile_entries = load_vehicle_profile_entries([vehicles_dir])
    except (OSError, json.JSONDecodeError, ValueError) as error:
        result["issues"].append(f"vehicle profiles could not be loaded: {error}")
        return result

    for profile_path, profile in profile_entries:
        if str(profile.get("id", "")).strip() == selected_vehicle:
            result["ok"] = True
            result["path"] = str(profile_path)
            result["label"] = str(profile.get("label", ""))
            return result

    result["issues"].append(f"selected vehicle profile is not installed: {selected_vehicle}")
    return result


def vehicle_profiles_dir(environ: Mapping[str, str]) -> Path:
    configured = str(environ.get("HEADUNIT_HUD_VEHICLES_DIR", "")).strip()
    if configured:
        return Path(configured)
    app_dir = str(environ.get("HEADUNIT_HUD_APP_DIR", "")).strip()
    if app_dir:
        return Path(app_dir) / "vehicles"
    return ROOT_DIR / "vehicles"


def append_unique(target: list[str], values: Any) -> None:
    for value in values or []:
        text = str(value)
        if text not in target:
            target.append(text)


def format_report(report: Mapping[str, Any]) -> str:
    acceptance = report["acceptance"]
    first_run = report["first_run"]
    vehicle_profile = report["vehicle_profile"]
    live_input = "not-probed"
    if acceptance["probe_inputs_required"]:
        live_input = "yes" if acceptance["live_input_ready"] else "no"
    lines = [
        f"Pi acceptance ready for car: {'yes' if acceptance['ready_for_car'] else 'no'}",
        f"Standalone without Android bridge: {'yes' if acceptance['standalone_ready'] else 'no'}",
        f"Android bridge: {'optional' if acceptance['bridge_optional'] else 'required'}",
        f"Layout: {'OK' if acceptance['layout_ready'] else 'FAIL'} - {first_run['layout']['detail']}",
        f"Display config: {first_run['display']['width']}x{first_run['display']['height']}",
        f"Vehicle profile: {'OK' if acceptance['vehicle_profile_ready'] else 'FAIL'} ({vehicle_profile['selected_vehicle'] or 'not-selected'})",
        f"OBD/iCar configured: {'yes' if first_run['obd']['configured'] else 'no'} ({first_run['obd']['transport']})",
        f"CANable configured: {'yes' if first_run['can']['configured'] else 'no'} ({first_run['can']['channel'] or 'not-configured'})",
        f"Live OBD/CAN probe: {live_input}",
    ]
    if acceptance["issues"]:
        lines.append("Issues:")
        lines.extend(f"- {issue}" for issue in acceptance["issues"])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    env_file = preparse_env_file(argv)
    load_runtime_environment(env_file)
    args = build_parser().parse_args(argv)

    os.environ["HEADUNIT_HUD_LAYOUT"] = args.layout
    os.environ["HEADUNIT_HUD_WIDTH"] = str(args.width)
    os.environ["HEADUNIT_HUD_HEIGHT"] = str(args.height)
    if args.require_handoff:
        os.environ["HEADUNIT_HUD_REQUIRE_HANDOFF"] = "1"

    report = build_acceptance_report(
        os.environ,
        probe_inputs=args.probe_inputs,
        obd_timeout=args.obd_timeout,
        can_timeout=args.can_timeout,
        probe_display_output=args.probe_display,
    )

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_report(report))

    if not args.no_write:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return 0 if report["acceptance"]["ready_for_car"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
