from __future__ import annotations

import unittest

from hud_pi.obd_polling import Elm327PollingMixin


class ParserOnlyElm327Source(Elm327PollingMixin):
    last_obd_request = ""
    last_obd_response = ""


class ObdPollingTest(unittest.TestCase):
    def test_polling_mixin_decodes_common_elm327_pid_responses(self) -> None:
        source = ParserOnlyElm327Source()

        self.assertEqual({"vehicle": {"source": "pi-obd", "obd_state": "live"}}, source._base_live_vehicle_update())
        self.assertEqual(42, source._parse_byte_pid_response("41 0D 2A", "410D"))
        self.assertEqual(50, source._parse_byte_pid_response("41 05 5A", "4105", offset=-40))
        self.assertEqual(1854, source._parse_rpm_response("41 0C 1C F8"))
        self.assertEqual(14.1, source._parse_adapter_voltage("14.1V"))
        self.assertEqual((True, 3), source._parse_mil_response("41 01 83 00"))


if __name__ == "__main__":
    unittest.main()
