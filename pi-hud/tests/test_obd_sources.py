from __future__ import annotations

import unittest

from hud_pi.obd_sources import BleElm327ObdSource, Elm327ObdSource


class ObdSourcesTest(unittest.TestCase):
    def test_obd_sources_expose_serial_and_ble_source_classes(self) -> None:
        serial_source = Elm327ObdSource(lambda _source, _update: None, "/dev/rfcomm0", baudrate=9600)
        ble_source = BleElm327ObdSource(
            lambda _source, _update: None,
            "AA:BB:CC:DD:EE:FF",
            "0000fff1-0000-1000-8000-00805f9b34fb",
            "0000fff2-0000-1000-8000-00805f9b34fb",
        )

        self.assertEqual("elm327-obd", serial_source.name)
        self.assertEqual("/dev/rfcomm0", serial_source.port)
        self.assertEqual(9600, serial_source.baudrate)
        self.assertEqual("ble-elm327-obd", ble_source.name)

    def test_obd_polling_parser_helpers_decode_common_pids(self) -> None:
        source = Elm327ObdSource(lambda _source, _update: None, "/dev/rfcomm0")

        self.assertEqual(42, source._parse_byte_pid_response("41 0D 2A", "410D"))
        self.assertEqual(50, source._parse_byte_pid_response("41 05 5A", "4105", offset=-40))
        self.assertEqual(1854, source._parse_rpm_response("41 0C 1C F8"))
        self.assertEqual(14.1, source._parse_adapter_voltage("14.1V"))
        self.assertEqual((True, 3), source._parse_mil_response("41 01 83 00"))


if __name__ == "__main__":
    unittest.main()
