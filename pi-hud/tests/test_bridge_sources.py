from __future__ import annotations

import unittest

from hud_pi.bridge_sources import BridgeDiscoveryResponder, BridgeUdpReceiver


class BridgeSourcesTest(unittest.TestCase):
    def test_bridge_sources_expose_udp_receiver_and_discovery_responder(self) -> None:
        receiver = BridgeUdpReceiver(lambda _source, _update: None, 4210, allow_diagnostic_packets=True)
        responder = BridgeDiscoveryResponder(lambda _source, _update: None, 4211, 4210)

        self.assertEqual("bridge-udp", receiver.name)
        self.assertEqual("Headunit Pi HUD", responder.name)
        self.assertTrue(receiver.allow_diagnostic_packets)
        self.assertEqual(4211, responder.discovery_port)
        self.assertEqual(4210, responder.hud_port)


if __name__ == "__main__":
    unittest.main()
