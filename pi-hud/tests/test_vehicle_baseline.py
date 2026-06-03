from __future__ import annotations

import unittest

from hud_pi.vehicle_baseline import (
    OBD_BASELINE_COMMANDS,
    build_obd_baseline_commands,
    can_message_to_record,
    collect_can_frames,
    collect_obd_baseline,
    profile_obd_probe_commands,
    response_ok,
    summarize_can_records,
)


class FakeCanMessage:
    def __init__(self, arbitration_id: int, data: bytes, timestamp: float = 123.456) -> None:
        self.arbitration_id = arbitration_id
        self.data = data
        self.dlc = len(data)
        self.timestamp = timestamp
        self.is_extended_id = False


class VehicleBaselineTest(unittest.TestCase):
    def test_response_ok_marks_common_elm_failures(self) -> None:
        self.assertTrue(response_ok("7E8 04 41 0C 1C F8"))
        self.assertFalse(response_ok(""))
        self.assertFalse(response_ok("NO DATA"))
        self.assertFalse(response_ok("UNABLE TO CONNECT"))
        self.assertFalse(response_ok("?"))

    def test_collect_obd_baseline_records_commands_in_order(self) -> None:
        responses = {
            "ATI": "ELM327 v1.5",
            "0100": "41 00 BE 1F A8 13",
            "03": "NO DATA",
        }

        records = collect_obd_baseline(lambda command: responses[command], commands=["ATI", "0100", "03"])

        self.assertEqual(["ATI", "0100", "03"], [record["command"] for record in records])
        self.assertEqual([True, True, False], [record["ok"] for record in records])
        self.assertEqual("NO DATA", records[2]["response"])

    def test_default_obd_baseline_commands_cover_required_first_log_set(self) -> None:
        for command in ["ATI", "AT@1", "ATDP", "ATDPN", "ATRV", "0100", "0120", "0140", "0160", "0101", "010C", "010D", "0105", "0142", "0902", "03", "07", "0A"]:
            self.assertIn(command, OBD_BASELINE_COMMANDS)

    def test_profile_obd_probe_commands_flattens_enabled_command_sequences(self) -> None:
        profile = {
            "obd_probe_commands": [
                {
                    "label": "Engine ECU current data",
                    "commands": ["ATSH7E0", "ATCRA7E8", "2101"],
                },
                {
                    "label": "Disabled probe",
                    "enabled": False,
                    "commands": ["220104"],
                },
                "ATSH7C6",
            ]
        }

        self.assertEqual(["ATSH7E0", "ATCRA7E8", "2101", "ATSH7C6"], profile_obd_probe_commands(profile))

    def test_build_obd_baseline_commands_appends_profile_probes_after_standard_commands(self) -> None:
        profile = {"obd_probe_commands": [{"commands": ["ATSH7D1", "ATCRA7D9", "220104"]}]}

        commands = build_obd_baseline_commands(profile)

        self.assertEqual(OBD_BASELINE_COMMANDS, commands[: len(OBD_BASELINE_COMMANDS)])
        self.assertEqual(["ATSH7D1", "ATCRA7D9", "220104"], commands[-3:])

    def test_can_message_to_record_formats_id_dlc_and_data(self) -> None:
        record = can_message_to_record(FakeCanMessage(0x316, b"\x05\x20\x00\xFF"))

        self.assertEqual(790, record["arbitration_id"])
        self.assertEqual("0x316", record["id"])
        self.assertEqual(4, record["dlc"])
        self.assertEqual("05 20 00 FF", record["data"])
        self.assertEqual(123.456, record["timestamp"])
        self.assertFalse(record["extended"])

    def test_collect_can_frames_stops_at_max_frames(self) -> None:
        messages = [FakeCanMessage(0x100, b"\x01"), FakeCanMessage(0x101, b"\x02")]

        def recv(_timeout: float) -> FakeCanMessage | None:
            return messages.pop(0) if messages else None

        records = collect_can_frames(recv, duration_seconds=10.0, max_frames=2, now=lambda: 0.0)

        self.assertEqual(["0x100", "0x101"], [record["id"] for record in records])

    def test_summarize_can_records_groups_by_id_and_marks_changing_bytes(self) -> None:
        records = [
            {"timestamp": 1.0, "arbitration_id": 0x316, "id": "0x316", "dlc": 4, "data": "05 20 00 FF"},
            {"timestamp": 1.1, "arbitration_id": 0x316, "id": "0x316", "dlc": 4, "data": "05 21 00 FF"},
            {"timestamp": 1.2, "arbitration_id": 0x329, "id": "0x329", "dlc": 2, "data": "10 00"},
        ]

        summary = summarize_can_records(records)

        self.assertEqual(3, summary["frame_count"])
        self.assertEqual(2, summary["unique_id_count"])
        self.assertEqual(["0x316", "0x329"], [item["id"] for item in summary["ids"]])
        self.assertEqual(2, summary["ids"][0]["count"])
        self.assertEqual([1], summary["ids"][0]["changing_byte_indexes"])
        self.assertEqual(["05 20 00 FF", "05 21 00 FF"], summary["ids"][0]["sample_data"])


if __name__ == "__main__":
    unittest.main()
