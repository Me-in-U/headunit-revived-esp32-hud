from __future__ import annotations

import unittest

from hud_pi.obd import parse_dtc_response
from hud_pi.sources import Elm327ObdSource


class ObdDtcTest(unittest.TestCase):
    def test_parse_mode_03_stored_dtc_response(self) -> None:
        self.assertEqual(["P0133"], parse_dtc_response("43 01 33 00 00 00 00", "43"))

    def test_parse_multiple_dtc_pairs_and_stop_at_zero_pair(self) -> None:
        self.assertEqual(["P0133", "P0A0F"], parse_dtc_response("7E8 06 43 01 33 0A 0F 00 00", "43"))

    def test_parse_body_chassis_and_network_prefixes(self) -> None:
        self.assertEqual(["C1234", "B0567", "U1000"], parse_dtc_response("47 52 34 85 67 D0 00", "47"))

    def test_ignore_unrelated_response(self) -> None:
        self.assertEqual([], parse_dtc_response("41 0D 2A", "43"))

    def test_repeated_empty_dtc_responses_are_empty(self) -> None:
        self.assertEqual([], parse_dtc_response("43 00\n43 00", "43"))


class FakeSerialLink:
    def __init__(self, response: bytes | list[bytes]) -> None:
        self.responses = list(response) if isinstance(response, list) else [response]
        self.writes: list[bytes] = []

    def write(self, payload: bytes) -> None:
        self.writes.append(payload)

    def flush(self) -> None:
        pass

    def read_until(self, _terminator: bytes, size: int) -> bytes:
        if not self.responses:
            return b">"
        return self.responses.pop(0)[:size]


class Elm327ObdSourceTest(unittest.TestCase):
    def test_send_tracks_last_obd_request_and_response_for_debug_layouts(self) -> None:
        source = Elm327ObdSource(lambda _source, _update: None, "/dev/rfcomm0")
        link = FakeSerialLink(b"7E8 04 41 0C 1C F8\r>")

        response = source._send(link, "010C")

        self.assertEqual(b"010C\r", link.writes[0])
        self.assertEqual("7E8 04 41 0C 1C F8", response)
        self.assertEqual("010C", source.last_obd_request)
        self.assertEqual("7E8 04 41 0C 1C F8", source.last_obd_response)

    def test_read_voltage_falls_back_to_adapter_voltage_when_pid_0142_is_missing(self) -> None:
        source = Elm327ObdSource(lambda _source, _update: None, "/dev/rfcomm0")
        link = FakeSerialLink([b"NO DATA\r>", b"14.1V\r>"])

        voltage = source._read_voltage(link)

        self.assertEqual(14.1, voltage)
        self.assertEqual([b"0142\r", b"ATRV\r"], link.writes)
        self.assertEqual("ATRV", source.last_obd_request)
        self.assertEqual("14.1V", source.last_obd_response)

    def test_base_live_vehicle_update_labels_obd_as_primary_source(self) -> None:
        source = Elm327ObdSource(lambda _source, _update: None, "/dev/rfcomm0")

        self.assertEqual({"vehicle": {"source": "pi-obd", "obd_state": "live"}}, source._base_live_vehicle_update())


if __name__ == "__main__":
    unittest.main()
