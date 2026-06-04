from __future__ import annotations

import unittest

from hud_pi.vehicle_baseline import (
    OBD_BASELINE_COMMANDS,
    build_obd_baseline_commands,
    collect_obd_baseline,
    profile_obd_probe_commands,
    response_ok,
)


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

if __name__ == "__main__":
    unittest.main()
