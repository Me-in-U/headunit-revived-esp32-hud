#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PI_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = PI_DIR.parent
if str(PI_DIR) not in sys.path:
    sys.path.insert(0, str(PI_DIR))

from hud_pi.diagnostics_can import open_socketcan_bus
from hud_pi.diagnostics_common import compact_response, load_env_file
from hud_pi.diagnostics_obd import run_ble_elm_commands, send_elm_command
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
    parser.add_argument("--scenario", default=os.environ.get("HEADUNIT_HUD_BASELINE_SCENARIO", ""))
    parser.add_argument("--can-channel", default=os.environ.get("HEADUNIT_HUD_CAN_CHANNEL", ""))
    parser.add_argument("--can-duration", type=float, default=float(os.environ.get("HEADUNIT_HUD_CAN_BASELINE_DURATION", "30.0")))
    parser.add_argument("--can-max-frames", type=int, default=int(os.environ.get("HEADUNIT_HUD_CAN_BASELINE_MAX_FRAMES", "20000")))
    parser.add_argument("--skip-obd", action="store_true")
    parser.add_argument("--skip-can", action="store_true")
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


def can_message_to_record(message: Any) -> dict[str, Any]:
    arbitration_id = int(message.arbitration_id)
    data = bytes(message.data)
    return {
        "timestamp": getattr(message, "timestamp", None),
        "arbitration_id": arbitration_id,
        "id": f"0x{arbitration_id:X}",
        "extended": bool(getattr(message, "is_extended_id", False)),
        "dlc": int(getattr(message, "dlc", len(data))),
        "data": " ".join(f"{byte:02X}" for byte in data),
    }


def collect_can(args: argparse.Namespace) -> dict[str, Any]:
    if args.skip_can:
        return {"configured": False, "records": [], "error": "skipped"}
    if not args.can_channel:
        return {"configured": False, "records": [], "error": "skipped"}
    try:
        import can
    except ImportError:
        return {
            "configured": True,
            "transport": "socketcan",
            "channel": args.can_channel,
            "duration_seconds": args.can_duration,
            "records": [],
            "error": "python-can-missing",
        }

    records: list[dict[str, Any]] = []
    bus = None
    error = ""
    started_at = datetime.now(timezone.utc).isoformat()
    started_monotonic = time.monotonic()
    deadline = started_monotonic + max(0.0, args.can_duration)
    max_frames = max(0, args.can_max_frames)
    try:
        bus = open_socketcan_bus(can, args.can_channel)
        while time.monotonic() < deadline and len(records) < max_frames:
            remaining = max(0.0, deadline - time.monotonic())
            message = bus.recv(timeout=min(0.5, remaining))
            if message is None:
                continue
            records.append(can_message_to_record(message))
    except Exception as exc:
        error = exc.__class__.__name__
    finally:
        if bus is not None:
            shutdown = getattr(bus, "shutdown", None)
            if callable(shutdown):
                shutdown()

    elapsed = time.monotonic() - started_monotonic
    result: dict[str, Any] = {
        "configured": True,
        "transport": "socketcan",
        "channel": args.can_channel,
        "started_at": started_at,
        "duration_seconds": round(elapsed, 3),
        "requested_duration_seconds": args.can_duration,
        "max_frames": max_frames,
        "frame_count": len(records),
        "truncated": len(records) >= max_frames if max_frames else False,
        "records": records,
    }
    if error:
        result["error"] = error
    return result


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
            "scenario": args.scenario,
            "obd_command_count": len(obd_commands),
            "can_analysis": "Use this baseline for raw evidence, then inspect changing bytes in the Windows editor CAN Analysis tab before deploying confirmed can_signals.",
        },
        "obd": collect_obd(args, obd_commands),
        "can": collect_can(args),
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
