from __future__ import annotations

import argparse
from pathlib import Path

from .layout import load_layout
from .layout_verifier import verify_layout_file


def default_layout_path() -> Path:
    return Path(__file__).resolve().parents[2] / "layouts" / "avante_hd_2010_default.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="1920x480 Raspberry Pi HUD runtime")
    parser.add_argument("--layout", default=str(default_layout_path()), help="Layout JSON file")
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--windowed", action="store_true", help="Use windowed mode instead of fullscreen")
    parser.add_argument("--udp-port", type=int, default=4210, help="Android bridge UDP port")
    parser.add_argument("--discovery-port", type=int, default=4211, help="Android bridge discovery UDP port")
    parser.add_argument("--disable-discovery", action="store_true", help="Do not answer Android bridge discovery probes")
    parser.add_argument("--allow-diagnostic-udp", action="store_true", help="Accept DTC/debug UDP packets for field investigation")
    parser.add_argument("--obd-port", default="", help="ELM327 serial/rfcomm port, e.g. /dev/rfcomm0")
    parser.add_argument("--obd-baud", type=int, default=38400)
    parser.add_argument("--obd-ble-mac", default="", help="ELM327 BLE adapter MAC address")
    parser.add_argument("--obd-ble-rx-uuid", default="", help="ELM327 BLE notify characteristic UUID, adapter to Pi")
    parser.add_argument("--obd-ble-tx-uuid", default="", help="ELM327 BLE write characteristic UUID, Pi to adapter")
    parser.add_argument("--can-channel", default="", help="SocketCAN channel, e.g. can0")
    parser.add_argument("--dummy", action="store_true", help="Force dummy vehicle data")
    parser.add_argument("--language", default="", help="HUD language: ko or en. Empty uses the layout language.")
    parser.add_argument("--require-layout-handoff", action="store_true", help="Require editor-generated Pi layout handoff metadata")
    return parser


def obd_configured(args: argparse.Namespace) -> bool:
    return bool(args.obd_port or args.obd_ble_mac)


def can_configured(args: argparse.Namespace) -> bool:
    return bool(args.can_channel)


def dummy_enabled(args: argparse.Namespace) -> bool:
    return bool(args.dummy or (not obd_configured(args) and not can_configured(args)))


def load_runtime_layout(args: argparse.Namespace) -> dict:
    result = verify_layout_file(
        args.layout,
        width=args.width,
        height=args.height,
        require_handoff=args.require_layout_handoff,
    )
    if not result.ok:
        raise ValueError("; ".join(result.errors))
    return load_layout(args.layout)
