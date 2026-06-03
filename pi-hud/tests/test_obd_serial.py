from __future__ import annotations

import unittest

from hud_pi.obd_serial import Elm327ObdSource


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


class ObdSerialTest(unittest.TestCase):
    def test_serial_source_tracks_last_request_and_response(self) -> None:
        source = Elm327ObdSource(lambda _source, _update: None, "/dev/rfcomm0")
        link = FakeSerialLink(b"7E8 04 41 0C 1C F8\r>")

        response = source._send(link, "010C")

        self.assertEqual(b"010C\r", link.writes[0])
        self.assertEqual("7E8 04 41 0C 1C F8", response)
        self.assertEqual("010C", source.last_obd_request)
        self.assertEqual("7E8 04 41 0C 1C F8", source.last_obd_response)

    def test_serial_source_reads_adapter_voltage_when_pid_voltage_is_missing(self) -> None:
        source = Elm327ObdSource(lambda _source, _update: None, "/dev/rfcomm0")
        link = FakeSerialLink([b"NO DATA\r>", b"14.1V\r>"])

        voltage = source._read_voltage(link)

        self.assertEqual(14.1, voltage)
        self.assertEqual([b"0142\r", b"ATRV\r"], link.writes)


if __name__ == "__main__":
    unittest.main()
