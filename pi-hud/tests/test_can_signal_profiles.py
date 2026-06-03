from __future__ import annotations

import unittest

from hud_pi.can_signal_profiles import is_confirmed_signal, selected_vehicle_can_signals


class CanSignalProfilesTest(unittest.TestCase):
    def test_selected_vehicle_can_signals_returns_deep_copied_confirmed_decodable_signals(self) -> None:
        original = {
            "confirmed": True,
            "frame_id": "0x316",
            "name": "vehicle.gear_actual",
            "start_byte": 1,
            "length": 1,
            "value_map": {"3": "D"},
        }
        layout = {
            "selected_vehicle": "car_a",
            "vehicles": [
                {
                    "id": "car_a",
                    "can_signals": [
                        original,
                        {"confirmed": False, "frame_id": "0x317", "name": "vehicle.unverified", "start_byte": 0, "length": 1},
                        {"confirmed": True, "frame_id": "bad", "name": "vehicle.bad", "start_byte": 0, "length": 1},
                    ],
                }
            ],
        }

        signals = selected_vehicle_can_signals(layout)
        signals[0]["value_map"]["3"] = "Drive"

        self.assertEqual(1, len(signals))
        self.assertEqual("D", original["value_map"]["3"])
        self.assertTrue(is_confirmed_signal(original))
        self.assertFalse(is_confirmed_signal({"confirmed": True, "frame_id": "0x316", "name": "vehicle.missing_shape"}))


if __name__ == "__main__":
    unittest.main()
