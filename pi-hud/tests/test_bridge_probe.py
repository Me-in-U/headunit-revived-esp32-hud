from __future__ import annotations

import json
import socket
import threading
import time
import unittest

from hud_pi.bridge_probe import (
    build_discovery_probe,
    discover_pi_hud,
    parse_discovery_hello,
    send_sample_bridge_packets,
)
from hud_pi.discovery import DEVICE_KIND_PI_HUD
from hud_pi.sources import BridgeDiscoveryResponder, BridgeUdpReceiver


def free_udp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class BridgeProbeTest(unittest.TestCase):
    def test_build_discovery_probe_matches_android_probe_contract(self) -> None:
        packet = json.loads(build_discovery_probe().decode("utf-8"))

        self.assertEqual({"type": "headunit_hud_discover"}, packet)

    def test_parse_discovery_hello_requires_pi_hud_device_kind(self) -> None:
        hello = parse_discovery_hello(
            b'{"type":"headunit_hud_hello","name":"Headunit Pi HUD","ip":"192.168.1.50","udp_port":4210,"device_kind":"pi_hud"}',
            source_host="192.168.1.50",
        )

        self.assertEqual("Headunit Pi HUD", hello.name)
        self.assertEqual("192.168.1.50", hello.host)
        self.assertEqual(4210, hello.udp_port)
        self.assertEqual(DEVICE_KIND_PI_HUD, hello.device_kind)

        with self.assertRaises(ValueError):
            parse_discovery_hello(b'{"type":"headunit_hud_hello","udp_port":4210,"device_kind":"esp32"}')

    def test_discover_pi_hud_finds_local_responder(self) -> None:
        discovery_port = free_udp_port()
        hud_port = free_udp_port()
        received = []
        responder = BridgeDiscoveryResponder(lambda source, update: received.append((source, update)), discovery_port, hud_port)
        responder.start()
        try:
            deadline = time.monotonic() + 2
            while not received and time.monotonic() < deadline:
                time.sleep(0.01)

            hello = discover_pi_hud("127.0.0.1", discovery_port=discovery_port, timeout=2.0)

            self.assertEqual(hud_port, hello.udp_port)
            self.assertEqual(DEVICE_KIND_PI_HUD, hello.device_kind)
        finally:
            responder.stop()
            responder.join(timeout=1.0)

    def test_send_sample_bridge_packets_updates_receiver_nav_and_backup_speed(self) -> None:
        udp_port = free_udp_port()
        received: list[tuple[str, dict]] = []
        event = threading.Event()

        def callback(source: str, update: dict) -> None:
            received.append((source, update))
            if len(received) >= 2:
                event.set()

        receiver = BridgeUdpReceiver(callback, udp_port)
        receiver.start()
        try:
            self.assertTrue(receiver.ready_event.wait(1.0))
            send_sample_bridge_packets("127.0.0.1", udp_port, speed_kmh=57)
            self.assertTrue(event.wait(2.0))

            sources = [source for source, _update in received]
            self.assertIn("bridge_nav", sources)
            self.assertIn("bridge_speed", sources)
            updates = [update for _source, update in received]
            self.assertIn({"vehicle": {"speed_kmh_backup": 57}}, updates)
            self.assertTrue(any(update.get("nav", {}).get("instruction") == "우회전" for update in updates))
        finally:
            receiver.stop()
            receiver.join(timeout=1.0)

    def test_receiver_ignores_stale_sequenced_bridge_packets(self) -> None:
        udp_port = free_udp_port()
        received: list[tuple[str, dict]] = []
        event = threading.Event()

        def callback(source: str, update: dict) -> None:
            received.append((source, update))
            event.set()

        receiver = BridgeUdpReceiver(callback, udp_port)
        receiver.start()
        try:
            self.assertTrue(receiver.ready_event.wait(1.0))
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                for packet in (
                    {"seq": 20, "type": "speed", "speed_kmh": 80},
                    {"seq": 19, "type": "speed", "speed_kmh": 12},
                    {"seq": 20, "type": "speed", "speed_kmh": 13},
                ):
                    sock.sendto(json.dumps(packet).encode("utf-8"), ("127.0.0.1", udp_port))

            self.assertTrue(event.wait(1.0))
            time.sleep(0.2)

            self.assertEqual([("bridge_speed", {"vehicle": {"speed_kmh_backup": 80}})], received)
        finally:
            receiver.stop()
            receiver.join(timeout=1.0)


if __name__ == "__main__":
    unittest.main()
