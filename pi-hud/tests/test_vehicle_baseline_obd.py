from __future__ import annotations

import unittest

from hud_pi.vehicle_baseline_obd import (
    OBD_BASELINE_COMMANDS,
    build_obd_baseline_commands,
    collect_obd_baseline,
    profile_obd_probe_commands,
    response_ok,
)


class VehicleBaselineObdTest(unittest.TestCase):
    def test_obd_baseline_helpers_collect_commands_and_profile_probe_extensions(self) -> None:
        responses = {
            "ATI": "ELM327 v1.5",
            "0100": "41 00 BE 1F A8 13",
            "03": "NO DATA",
        }

        records = collect_obd_baseline(lambda command: responses[command], commands=["ATI", "0100", "03"])

        self.assertEqual(["ATI", "0100", "03"], [record["command"] for record in records])
        self.assertEqual([True, True, False], [record["ok"] for record in records])
        self.assertTrue(response_ok("7E8 04 41 0C 1C F8"))
        self.assertFalse(response_ok("UNABLE TO CONNECT"))

        profile = {"obd_probe_commands": [{"commands": ["ATSH7D1", "ATCRA7D9"]}, "220104"]}
        self.assertEqual(["ATSH7D1", "ATCRA7D9", "220104"], profile_obd_probe_commands(profile))
        self.assertEqual(OBD_BASELINE_COMMANDS, build_obd_baseline_commands(profile)[: len(OBD_BASELINE_COMMANDS)])
        self.assertEqual(["ATSH7D1", "ATCRA7D9", "220104"], build_obd_baseline_commands(profile)[-3:])


if __name__ == "__main__":
    unittest.main()
