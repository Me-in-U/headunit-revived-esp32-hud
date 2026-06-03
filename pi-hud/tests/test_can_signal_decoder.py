from __future__ import annotations

import unittest

from hud_pi.can_signal_decoder import decode_can_signals, merge_nested_update


class CanSignalDecoderTest(unittest.TestCase):
    def test_decode_can_signals_preserves_byte_bit_mapping_and_nested_updates(self) -> None:
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
                "frame_id": "0x316",
                "name": "warnings.abs",
                "start_byte": 0,
                "start_bit": 2,
                "bit_length": 1,
                "value_map": {"0": False, "1": True},
            },
            {
                "confirmed": True,
                "frame_id": "0x999",
                "name": "vehicle.ignored",
                "start_byte": 0,
                "length": 1,
            },
        ]

        update = decode_can_signals(0x316, bytes([0b00000100, 0x03]), signals)

        self.assertEqual({"vehicle": {"gear_actual": "D"}, "warnings": {"abs": True}}, update)

    def test_merge_nested_update_preserves_existing_nested_keys(self) -> None:
        target = {"vehicle": {"speed_kmh": 42}}

        merge_nested_update(target, {"vehicle": {"gear_actual": "D"}, "warnings": {"abs": True}})

        self.assertEqual({"vehicle": {"speed_kmh": 42, "gear_actual": "D"}, "warnings": {"abs": True}}, target)


if __name__ == "__main__":
    unittest.main()
