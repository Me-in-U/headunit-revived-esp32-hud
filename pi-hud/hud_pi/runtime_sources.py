from __future__ import annotations

import argparse
from typing import Any

from .can_signals import selected_vehicle_can_signals
from .runtime_config import dummy_enabled
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
