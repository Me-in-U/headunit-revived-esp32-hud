#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PI_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = PI_DIR.parent
if str(PI_DIR) not in sys.path:
    sys.path.insert(0, str(PI_DIR))

from hud_pi.diagnostics import compact_response, load_env_file, run_ble_elm_commands, send_elm_command
from hud_pi.vehicle_baseline import OBD_BASELINE_COMMANDS, build_obd_baseline_commands, collect_obd_baseline, response_ok


def default_env_file_path() -> str:
    configured = os.environ.get("HEADUNIT_HUD_ENV_FILE", "").strip()
    if configured:
        return configured
    return "/etc/headunit-pi-hud.env"


def load_runtime_environment() -> list[str]:
    return load_env_file(default_env_file_path(), os.environ)


def default_output_path() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return str(ROOT_DIR / "vehicle-baseline" / f"{stamp}-avante-hd-baseline.json")


def default_vehicle_profile_path() -> str:
    return str(ROOT_DIR / "vehicles" / "avante_hd_2010_1_6_at.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect first-run OBD evidence for the Raspberry Pi HUD")
    parser.add_argument("--obd-port", default=os.environ.get("HEADUNIT_HUD_OBD_PORT", ""))
    parser.add_argument("--obd-baud", type=int, default=int(os.environ.get("HEADUNIT_HUD_OBD_BAUD", "38400")))
    parser.add_argument("--obd-timeout", type=float, default=2.0)
    parser.add_argument("--obd-ble-mac", default=os.environ.get("HEADUNIT_HUD_OBD_BLE_MAC", ""))
    parser.add_argument("--obd-ble-rx-uuid", default=os.environ.get("HEADUNIT_HUD_OBD_BLE_RX_UUID", ""))
    parser.add_argument("--obd-ble-tx-uuid", default=os.environ.get("HEADUNIT_HUD_OBD_BLE_TX_UUID", ""))
    parser.add_argument("--vehicle-profile", default=os.environ.get("HEADUNIT_HUD_VEHICLE_PROFILE", default_vehicle_profile_path()))
    parser.add_argument("--output", default=default_output_path())
    parser.add_argument("--skip-obd", action="store_true")
    return parser


def load_vehicle_profile(path: str) -> dict[str, Any]:
    if not path:
        return {}
    profile_path = Path(path)
    if not profile_path.exists():
        return {}
    with profile_path.open("r", encoding="utf-8") as handle:
        profile = json.load(handle)
    return profile if isinstance(profile, dict) else {}


def build_obd_commands(args: argparse.Namespace) -> list[str]:
    return build_obd_baseline_commands(load_vehicle_profile(args.vehicle_profile))


def collect_obd_ble_baseline(args: argparse.Namespace, commands: list[str] | tuple[str, ...] = OBD_BASELINE_COMMANDS) -> list[dict[str, Any]]:
    try:
        responses = run_ble_elm_commands(
            args.obd_ble_mac,
            args.obd_ble_rx_uuid,
            args.obd_ble_tx_uuid,
            commands,
            timeout=args.obd_timeout,
        )
    except Exception as exc:
        return [
            {
                "command": "connect",
                "response": "",
                "ok": False,
                "error": exc.__class__.__name__,
            }
        ]

    records: list[dict[str, Any]] = []
    for command, response in zip(commands, responses):
        compacted = compact_response(response)
        records.append(
            {
                "command": command,
                "response": compacted,
                "ok": response_ok(compacted),
            }
        )
    return records


def collect_obd(args: argparse.Namespace, commands: list[str] | tuple[str, ...] = OBD_BASELINE_COMMANDS) -> dict[str, Any]:
    if args.skip_obd:
        return {"configured": False, "records": [], "error": "skipped"}
    if not args.obd_port and args.obd_ble_mac:
        return {
            "configured": True,
            "transport": "ble",
            "mac": args.obd_ble_mac,
            "rx_uuid": args.obd_ble_rx_uuid,
            "tx_uuid": args.obd_ble_tx_uuid,
            "records": collect_obd_ble_baseline(args, commands),
        }
    if not args.obd_port:
        return {"configured": False, "records": [], "error": "skipped"}
    try:
        import serial
    except ImportError:
        return {"configured": True, "transport": "serial", "port": args.obd_port, "baud": args.obd_baud, "records": [], "error": "pyserial-missing"}

    try:
        with serial.Serial(args.obd_port, args.obd_baud, timeout=args.obd_timeout, write_timeout=args.obd_timeout) as link:
            send_elm_command(link, "ATZ")
            send_elm_command(link, "ATE0")
            send_elm_command(link, "ATL0")
            records = collect_obd_baseline(lambda command: send_elm_command(link, command), commands)
    except OSError as exc:
        return {"configured": True, "transport": "serial", "port": args.obd_port, "baud": args.obd_baud, "records": [], "error": exc.__class__.__name__}

    return {
        "configured": True,
        "transport": "serial",
        "port": args.obd_port,
        "baud": args.obd_baud,
        "records": records,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    profile = load_vehicle_profile(args.vehicle_profile)
    obd_commands = build_obd_baseline_commands(profile)
    return {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "vehicle": profile.get("id", "avante_hd_2010_1_6_at"),
        "notes": {
            "dlc_pins": [16, 15, 14, 12, 8, 6, 5, 4, 3],
            "android_role": "navigation_and_backup_speed_only",
            "vehicle_profile": args.vehicle_profile,
            "obd_command_count": len(obd_commands),
            "can_analysis": "Use the Windows editor CAN Analysis tab before deploying confirmed can_signals.",
        },
        "obd": collect_obd(args, obd_commands),
    }


def main(argv: list[str] | None = None) -> int:
    load_runtime_environment()
    args = build_parser().parse_args(argv)
    report = build_report(args)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(f"[OK] baseline written: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
