from __future__ import annotations

import argparse
import os
import signal
import sys
import threading
from pathlib import Path
from typing import Any

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from .can_signals import selected_vehicle_can_signals
from .layout import load_layout
from .layout_verifier import verify_layout_file
from .renderer import HudRenderer, normalize_language
from .sources import (
    BleElm327ObdSource,
    BridgeDiscoveryResponder,
    BridgeUdpReceiver,
    DummyVehicleSource,
    Elm327ObdSource,
    SocketCanSource,
    StateCallback,
    SourceThread,
)
from .state import build_initial_state


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


def build_vehicle_sources(args: argparse.Namespace, merge: StateCallback, layout: dict[str, Any] | None = None) -> list[SourceThread]:
    sources: list[SourceThread] = [BridgeUdpReceiver(merge, args.udp_port, allow_diagnostic_packets=args.allow_diagnostic_udp)]
    if not args.disable_discovery:
        sources.append(BridgeDiscoveryResponder(merge, args.discovery_port, args.udp_port))
    if args.obd_port:
        sources.append(Elm327ObdSource(merge, args.obd_port, args.obd_baud))
    elif args.obd_ble_mac:
        sources.append(BleElm327ObdSource(merge, args.obd_ble_mac, args.obd_ble_rx_uuid, args.obd_ble_tx_uuid))
    if args.can_channel:
        sources.append(SocketCanSource(merge, args.can_channel, selected_vehicle_can_signals(layout or {})))
    if dummy_enabled(args):
        sources.append(DummyVehicleSource(merge))
    return sources


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


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        layout = load_runtime_layout(args)
    except ValueError as exc:
        print(f"Layout validation failed: {exc}", file=sys.stderr)
        return 2
    if args.language:
        layout["language"] = normalize_language(args.language, fallback=str(layout.get("language", "en")))
    use_dummy = dummy_enabled(args)
    state = build_initial_state(
        layout,
        obd_configured=obd_configured(args),
        can_configured=can_configured(args),
        dummy_enabled=use_dummy,
    )
    lock = threading.Lock()

    def merge(source: str, update: dict) -> None:
        with lock:
            state.merge(source, update)

    sources = build_vehicle_sources(args, merge, layout=layout)

    for source in sources:
        source.start()

    pygame.init()
    flags = 0 if args.windowed else pygame.FULLSCREEN
    screen = pygame.display.set_mode((args.width, args.height), flags)
    pygame.display.set_caption("Headunit Pi HUD")
    renderer = HudRenderer(layout, screen)
    clock = pygame.time.Clock()
    running = True

    def stop(_signum: int, _frame: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q):
                running = False
        with lock:
            state.mark_stale_sources()
            renderer.render(state)
        pygame.display.flip()
        clock.tick(30)

    for source in sources:
        source.stop()
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
