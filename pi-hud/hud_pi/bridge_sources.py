from __future__ import annotations

import json
import socket
import time
from typing import Any

from .bridge_packets import SequencedPacketGate
from .discovery import build_discovery_hello, local_ip_for, parse_discovery_probe
from .source_threads import SourceThread, StateCallback
from .state_packets import normalize_packet


class BridgeUdpReceiver(SourceThread):
    def __init__(self, callback: StateCallback, port: int, allow_diagnostic_packets: bool = False) -> None:
        super().__init__(callback, "bridge-udp")
        self.port = port
        self.allow_diagnostic_packets = allow_diagnostic_packets
        self.packet_gate = SequencedPacketGate()

    @property
    def last_sequence(self) -> int | None:
        return self.packet_gate.last_sequence

    def run(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("", self.port))
            sock.settimeout(0.5)
            self.ready_event.set()
            while not self.stop_event.is_set():
                try:
                    data, _addr = sock.recvfrom(8192)
                except socket.timeout:
                    continue
                try:
                    packet = json.loads(data.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
                if not self._accept_packet(packet):
                    continue
                source, update = normalize_packet(packet, allow_diagnostic_packets=self.allow_diagnostic_packets)
                self.callback(source, update)
        finally:
            sock.close()

    def _accept_packet(self, packet: Any) -> bool:
        return self.packet_gate.accepts(packet)


class BridgeDiscoveryResponder(SourceThread):
    def __init__(self, callback: StateCallback, discovery_port: int, hud_port: int, name: str = "Headunit Pi HUD") -> None:
        super().__init__(callback, "bridge-discovery")
        self.discovery_port = discovery_port
        self.hud_port = hud_port
        self.name = name

    def run(self) -> None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(("", self.discovery_port))
            sock.settimeout(0.5)
        except OSError as exc:
            self.callback("bridge", {"nav": {"discovery_state": f"error:{exc.__class__.__name__}"}})
            self.ready_event.set()
            return

        last_hello_at = 0.0
        self.ready_event.set()
        self.callback("bridge", {"nav": {"discovery_state": "listening"}})
        while not self.stop_event.is_set():
            now = time.monotonic()
            if now - last_hello_at >= 5.0:
                last_hello_at = now
                self._send_hello(sock, ("255.255.255.255", self.discovery_port))
            try:
                data, addr = sock.recvfrom(2048)
            except socket.timeout:
                continue
            if not parse_discovery_probe(data):
                continue
            self._send_hello(sock, addr)
        sock.close()

    def _send_hello(self, sock: socket.socket, addr: tuple[str, int]) -> None:
        ip_address = local_ip_for(addr[0])
        payload = build_discovery_hello(self.name, ip_address, self.hud_port)
        try:
            sock.sendto(payload, addr)
        except OSError:
            return
