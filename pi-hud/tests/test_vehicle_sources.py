from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path

from hud_pi.sources import DummyVehicleSource


class VehicleSourcesTest(unittest.TestCase):
    def test_dummy_vehicle_source_labels_vehicle_source_as_dummy(self) -> None:
        received: list[tuple[str, dict]] = []
        event = threading.Event()

        def callback(source: str, update: dict) -> None:
            received.append((source, update))
            event.set()

        source = DummyVehicleSource(callback)
        source.start()
        try:
            self.assertTrue(event.wait(1.0))
        finally:
            source.stop()
            source.join(timeout=1.0)

        self.assertEqual("dummy", received[0][0])
        self.assertEqual("dummy", received[0][1]["vehicle"]["source"])

    def test_ble_obd_options_create_pi_obd_source_without_dummy_data(self) -> None:
        from hud_pi.main import build_parser, build_vehicle_sources, obd_configured
        from hud_pi.sources import BleElm327ObdSource, DummyVehicleSource, Elm327ObdSource

        args = build_parser().parse_args(
            [
                "--obd-ble-mac",
                "AA:BB:CC:DD:EE:FF",
                "--obd-ble-rx-uuid",
                "0000fff1-0000-1000-8000-00805f9b34fb",
                "--obd-ble-tx-uuid",
                "0000fff2-0000-1000-8000-00805f9b34fb",
            ]
        )
        sources = build_vehicle_sources(args, lambda _source, _update: None)

        self.assertTrue(obd_configured(args))
        self.assertTrue(any(isinstance(source, BleElm327ObdSource) for source in sources))
        self.assertFalse(any(isinstance(source, Elm327ObdSource) for source in sources))
        self.assertFalse(any(isinstance(source, DummyVehicleSource) for source in sources))

    def test_runtime_parser_accepts_required_layout_handoff(self) -> None:
        from hud_pi.main import build_parser

        args = build_parser().parse_args(["--require-layout-handoff"])

        self.assertTrue(args.require_layout_handoff)

    def test_runtime_can_enable_diagnostic_udp_packets_for_field_investigation(self) -> None:
        from hud_pi.main import build_parser, build_vehicle_sources
        from hud_pi.sources import BridgeUdpReceiver

        args = build_parser().parse_args(["--allow-diagnostic-udp"])
        sources = build_vehicle_sources(args, lambda _source, _update: None)

        receiver = next(source for source in sources if isinstance(source, BridgeUdpReceiver))
        self.assertTrue(receiver.allow_diagnostic_packets)

    def test_runtime_rejects_layout_without_handoff_when_required(self) -> None:
        from hud_pi.main import build_parser, load_runtime_layout

        with tempfile.TemporaryDirectory() as temp_dir:
            layout_path = Path(temp_dir) / "missing-handoff.json"
            layout = json.loads(Path("layouts/avante_hd_2010_default.json").read_text(encoding="utf-8"))
            layout.pop("pi_hud_handoff", None)
            layout_path.write_text(json.dumps(layout, ensure_ascii=False), encoding="utf-8")
            args = build_parser().parse_args(
                [
                    "--layout",
                    str(layout_path),
                    "--require-layout-handoff",
                ]
            )

            with self.assertRaisesRegex(ValueError, "pi_hud_handoff metadata is missing"):
                load_runtime_layout(args)

    def test_runtime_socketcan_source_receives_confirmed_selected_vehicle_signal_definitions(self) -> None:
        from hud_pi.main import build_parser, build_vehicle_sources
        from hud_pi.sources import SocketCanSource

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
        args = build_parser().parse_args(["--can-channel", "can0"])

        sources = build_vehicle_sources(args, lambda _source, _update: None, layout=layout)

        socketcan = next(source for source in sources if isinstance(source, SocketCanSource))
        self.assertEqual(
            [{"confirmed": True, "frame_id": "0x316", "name": "vehicle.gear_actual", "start_byte": 1, "length": 1}],
            socketcan.signal_definitions,
        )


if __name__ == "__main__":
    unittest.main()
