from __future__ import annotations

import unittest

from hud_pi.vehicle_baseline_can import can_message_to_record, summarize_can_records


class FakeCanMessage:
    def __init__(self, arbitration_id: int, data: bytes, timestamp: float = 123.456) -> None:
        self.arbitration_id = arbitration_id
        self.data = data
        self.dlc = len(data)
        self.timestamp = timestamp
        self.is_extended_id = False


class VehicleBaselineCanTest(unittest.TestCase):
    def test_can_baseline_helpers_format_records_and_summarize_changing_payload_bytes(self) -> None:
        record = can_message_to_record(FakeCanMessage(0x316, b"\x05\x20\x00\xFF"))

        self.assertEqual(790, record["arbitration_id"])
        self.assertEqual("0x316", record["id"])
        self.assertEqual("05 20 00 FF", record["data"])

        summary = summarize_can_records(
            [
                record,
                {"timestamp": 123.500, "arbitration_id": 0x316, "id": "0x316", "dlc": 4, "data": "05 21 00 FF"},
                {"timestamp": 123.600, "id": "0x329", "dlc": 2, "data": "10 00"},
            ]
        )

        self.assertEqual(3, summary["frame_count"])
        self.assertEqual(2, summary["unique_id_count"])
        self.assertEqual(["0x316", "0x329"], [item["id"] for item in summary["ids"]])
        self.assertEqual([1], summary["ids"][0]["changing_byte_indexes"])
        self.assertEqual(["05 20 00 FF", "05 21 00 FF"], summary["ids"][0]["sample_data"])


if __name__ == "__main__":
    unittest.main()
