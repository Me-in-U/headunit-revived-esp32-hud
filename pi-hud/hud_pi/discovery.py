from __future__ import annotations

import json
import socket
from typing import Any


DISCOVERY_PROBE_TYPE = "headunit_hud_discover"
DISCOVERY_HELLO_TYPE = "headunit_hud_hello"
DEVICE_KIND_PI_HUD = "pi_hud"


def parse_discovery_probe(data: bytes) -> bool:
    try:
        packet: Any = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    return isinstance(packet, dict) and packet.get("type") == DISCOVERY_PROBE_TYPE


def build_discovery_hello(name: str, ip_address: str, udp_port: int, device_kind: str = DEVICE_KIND_PI_HUD) -> bytes:
    return json.dumps(
        {
            "type": DISCOVERY_HELLO_TYPE,
            "name": name,
            "ip": ip_address,
            "udp_port": udp_port,
            "device_kind": device_kind,
        },
        separators=(",", ":"),
    ).encode("utf-8")


def local_ip_for(remote_host: str) -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect((remote_host, 9))
            return str(sock.getsockname()[0])
    except OSError:
        return "0.0.0.0"
