from __future__ import annotations

import unittest

from hud_pi.runtime_config import build_parser
from hud_pi.runtime_sources import build_vehicle_sources
from hud_pi.sources import BridgeDiscoveryResponder, BridgeUdpReceiver, DummyVehicleSource, SocketCanSource


class RuntimeSourcesTest(unittest.TestCase):
    def test_runtime_sources_wire_bridge_dummy_and_diagnostic_options(self) -> None:
        args = build_parser().parse_args(["--allow-diagnostic-udp"])
        sources = build_vehicle_sources(args, lambda _source, _update: None)

        self.assertTrue(any(isinstance(source, BridgeDiscoveryResponder) for source in sources))
        self.assertTrue(any(isinstance(source, DummyVehicleSource) for source in sources))
        receiver = next(source for source in sources if isinstance(source, BridgeUdpReceiver))
        self.assertTrue(receiver.allow_diagnostic_packets)

    def test_runtime_sources_pass_selected_vehicle_can_signals_to_socketcan(self) -> None:
        args = build_parser().parse_args(["--can-channel", "can0"])
        layout = {
            "selected_vehicle": "car_a",
            "vehicles": [
                {
                    "id": "car_a",
                    "label": "Car A",
                    "can_signals": [
                        {"confirmed": True, "frame_id": "0x316", "name": "vehicle.gear_actual", "start_byte": 1, "length": 1},
                        {"confirmed": False, "frame_id": "0x317", "name": "vehicle.unverified", "start_byte": 0, "length": 1},
                    ],
                }
            ],
        }

        sources = build_vehicle_sources(args, lambda _source, _update: None, layout=layout)

        socketcan = next(source for source in sources if isinstance(source, SocketCanSource))
        self.assertEqual(
            [{"confirmed": True, "frame_id": "0x316", "name": "vehicle.gear_actual", "start_byte": 1, "length": 1}],
            socketcan.signal_definitions,
        )


if __name__ == "__main__":
    unittest.main()
