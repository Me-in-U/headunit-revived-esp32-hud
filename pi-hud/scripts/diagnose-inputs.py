#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PI_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = PI_DIR.parent
if str(PI_DIR) not in sys.path:
    sys.path.insert(0, str(PI_DIR))

from hud_pi.diagnostics import format_result, layout_summary, load_env_file, probe_can, probe_obd, probe_obd_ble


def default_env_file_path() -> Path:
    configured = os.environ.get("HEADUNIT_HUD_ENV_FILE", "").strip()
    if configured:
        return Path(configured)
    return Path("/etc/headunit-pi-hud.env")


def load_runtime_environment() -> list[str]:
    return load_env_file(default_env_file_path(), os.environ)


def default_layout_path() -> str:
    return os.environ.get(
        "HEADUNIT_HUD_LAYOUT",
        str(ROOT_DIR / "layouts" / "avante_hd_2010_default.json"),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check Raspberry Pi HUD OBD/CAN inputs before launching the UI")
    parser.add_argument("--layout", default=default_layout_path(), help="Layout JSON path")
    parser.add_argument("--obd-port", default=os.environ.get("HEADUNIT_HUD_OBD_PORT", ""))
    parser.add_argument("--obd-baud", type=int, default=int(os.environ.get("HEADUNIT_HUD_OBD_BAUD", "38400")))
    parser.add_argument("--obd-ble-mac", default=os.environ.get("HEADUNIT_HUD_OBD_BLE_MAC", ""))
    parser.add_argument("--obd-ble-rx-uuid", default=os.environ.get("HEADUNIT_HUD_OBD_BLE_RX_UUID", ""))
    parser.add_argument("--obd-ble-tx-uuid", default=os.environ.get("HEADUNIT_HUD_OBD_BLE_TX_UUID", ""))
    parser.add_argument("--obd-ble-timeout", type=float, default=2.0)
    parser.add_argument("--can-channel", default=os.environ.get("HEADUNIT_HUD_CAN_CHANNEL", ""))
    parser.add_argument("--can-timeout", type=float, default=3.0)
    parser.add_argument("--skip-obd", action="store_true")
    parser.add_argument("--skip-can", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    load_runtime_environment()
    args = build_parser().parse_args(argv)
    failures = 0

    result = layout_summary(args.layout)
    print(format_result(result))
    if not result.ok:
        failures += 1

    if args.skip_obd:
        print("[SKIP] obd: skipped")
    elif args.obd_port:
        result = probe_obd(args.obd_port, args.obd_baud)
        print(format_result(result))
        if not result.ok:
            failures += 1
    elif args.obd_ble_mac:
        result = probe_obd_ble(args.obd_ble_mac, args.obd_ble_rx_uuid, args.obd_ble_tx_uuid, args.obd_ble_timeout)
        print(format_result(result))
        if not result.ok:
            failures += 1
    else:
        print("[SKIP] obd: no OBD port configured")

    if args.skip_can or not args.can_channel:
        print("[SKIP] can: no CAN channel configured")
    else:
        result = probe_can(args.can_channel, args.can_timeout)
        print(format_result(result))
        if not result.ok:
            failures += 1

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
