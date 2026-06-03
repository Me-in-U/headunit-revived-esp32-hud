from __future__ import annotations

import unittest

from hud_pi.can_signals import decode_can_signals, selected_vehicle_can_signals


class CanSignalsTest(unittest.TestCase):
    def test_selected_vehicle_can_signals_returns_confirmed_signal_definitions_only(self) -> None:
        layout = {
            "selected_vehicle": "car_a",
            "vehicles": [
                {
                    "id": "car_a",
                    "label": "Car A",
                    "can_signals": [
                        {"confirmed": True, "frame_id": "0x316", "name": "vehicle.gear_actual", "start_byte": 1, "length": 1},
                        {"confirmed": True, "frame_id": "0x420", "name": "warnings.abs", "start_byte": 0, "start_bit": 2, "bit_length": 1},
                        {"confirmed": False, "frame_id": "0x317", "name": "vehicle.unverified", "start_byte": 0, "length": 1},
                    ],
                }
            ],
        }

        signals = selected_vehicle_can_signals(layout)

        self.assertEqual(2, len(signals))
        self.assertEqual("vehicle.gear_actual", signals[0]["name"])
        self.assertEqual("warnings.abs", signals[1]["name"])

    def test_decode_can_signals_maps_matching_frame_bytes_into_nested_hud_state(self) -> None:
        signals = [
            {
                "confirmed": True,
                "frame_id": "0x316",
                "name": "vehicle.gear_actual",
                "start_byte": 1,
                "length": 1,
                "value_map": {"3": "D"},
            },
            {
                "confirmed": True,
                "frame_id": 0x316,
                "name": "vehicle.pedal_percent",
                "start_byte": 2,
                "length": 1,
                "scale": 0.5,
            },
        ]

        update = decode_can_signals(0x316, bytes([0x00, 0x03, 0x50]), signals)

        self.assertEqual(
            {
                "vehicle": {
                    "gear_actual": "D",
                    "pedal_percent": 40,
                }
            },
            update,
        )

    def test_decode_can_signals_maps_bit_fields_into_nested_hud_state(self) -> None:
        signals = [
            {
                "confirmed": True,
                "frame_id": "0x420",
                "name": "warnings.abs",
                "start_byte": 0,
                "start_bit": 2,
                "bit_length": 1,
                "value_map": {"0": False, "1": True},
            },
            {
                "confirmed": True,
                "frame_id": "0x420",
                "name": "vehicle.gear_actual",
                "start_byte": 1,
                "start_bit": 0,
                "bit_length": 3,
                "value_map": {"5": "D"},
            },
        ]

        update = decode_can_signals(0x420, bytes([0b00000100, 0b00000101]), signals)

        self.assertEqual(
            {
                "warnings": {"abs": True},
                "vehicle": {"gear_actual": "D"},
            },
            update,
        )

    def test_decode_can_signals_ignores_unconfirmed_and_non_matching_frames(self) -> None:
        signals = [
            {"confirmed": False, "frame_id": "0x316", "name": "vehicle.gear_actual", "start_byte": 1, "length": 1},
            {"confirmed": True, "frame_id": "0x999", "name": "vehicle.pedal_percent", "start_byte": 2, "length": 1},
        ]

        self.assertEqual({}, decode_can_signals(0x316, bytes([0x00, 0x03, 0x50]), signals))


if __name__ == "__main__":
    unittest.main()
