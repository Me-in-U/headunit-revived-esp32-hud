from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from typing import Any

from .discovery import DEVICE_KIND_PI_HUD, DISCOVERY_HELLO_TYPE, DISCOVERY_PROBE_TYPE


@dataclass(frozen=True)
class DiscoveryHello:
    name: str
    host: str
    udp_port: int
    device_kind: str
    source_host: str = ""


def build_discovery_probe() -> bytes:
    return json.dumps({"type": DISCOVERY_PROBE_TYPE}, separators=(",", ":")).encode("utf-8")


def parse_discovery_hello(data: bytes, source_host: str = "") -> DiscoveryHello:
    try:
        packet: Any = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid discovery hello json") from exc
    if not isinstance(packet, dict) or packet.get("type") != DISCOVERY_HELLO_TYPE:
        raise ValueError("packet is not a headunit_hud_hello")
    device_kind = str(packet.get("device_kind", ""))
    if device_kind != DEVICE_KIND_PI_HUD:
        raise ValueError(f"hello device_kind is not pi_hud: {device_kind or 'missing'}")
    udp_port = int(packet.get("udp_port", 0))
    if udp_port <= 0:
        raise ValueError("hello udp_port must be positive")
    json_ip = str(packet.get("ip", "")).strip()
    host = source_host or json_ip
    if not host:
        raise ValueError("hello host is missing")
    return DiscoveryHello(
        name=str(packet.get("name", "Headunit Pi HUD")),
        host=host,
        udp_port=udp_port,
        device_kind=device_kind,
        source_host=source_host,
    )


def discover_pi_hud(host: str, discovery_port: int = 4211, timeout: float = 3.0) -> DiscoveryHello:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(timeout)
        sock.sendto(build_discovery_probe(), (host, discovery_port))
        while True:
            data, addr = sock.recvfrom(2048)
            try:
                return parse_discovery_hello(data, source_host=str(addr[0]))
            except ValueError:
                continue


def send_sample_bridge_packets(host: str, udp_port: int, speed_kmh: int = 42) -> int:
    packets = [
        {
            "distance_meters": 300,
            "time_seconds": 25,
            "road": "강남대로",
            "action_text": "우회전",
            "instruction": "우회전",
            "turn_side": 2,
            "event_type": 4,
            "active": True,
        },
        {
            "type": "speed",
            "speed_kmh": speed_kmh,
        },
    ]
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        for packet in packets:
            payload = json.dumps(packet, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            sock.sendto(payload, (host, udp_port))
    return len(packets)
