from __future__ import annotations

import unittest

from hud_pi.diagnostics_obd import probe_obd_ble, send_elm_command


class FakeElmLink:
    def __init__(self, response: bytes) -> None:
        self.response = response
        self.writes: list[bytes] = []
        self.flushed = False

    def write(self, payload: bytes) -> None:
        self.writes.append(payload)

    def flush(self) -> None:
        self.flushed = True

    def read_until(self, _separator: bytes, size: int = 1024) -> bytes:
        return self.response[:size]


class DiagnosticsObdTest(unittest.TestCase):
    def test_send_elm_command_writes_ascii_command_and_compacts_prompt_response(self) -> None:
        link = FakeElmLink(b"ELM327 v1.5\r>")

        response = send_elm_command(link, "ATI")

        self.assertEqual([b"ATI\r"], link.writes)
        self.assertTrue(link.flushed)
        self.assertEqual("ELM327 v1.5", response)

    def test_probe_obd_ble_reports_missing_characteristics_without_connecting(self) -> None:
        result = probe_obd_ble("AA:BB:CC:DD:EE:FF", "", "")

        self.assertFalse(result.ok)
        self.assertEqual("obd-ble", result.name)
        self.assertEqual("missing RX/TX UUID", result.detail)


if __name__ == "__main__":
    unittest.main()
