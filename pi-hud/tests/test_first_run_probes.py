from __future__ import annotations

import unittest

from hud_pi.diagnostics import DiagnosticResult
from hud_pi.first_run_probes import display_probe_status, probe_input_status


class FirstRunProbesTest(unittest.TestCase):
    def test_probe_input_status_uses_injected_serial_obd_and_can_probe_functions(self) -> None:
        calls: list[tuple[str, tuple[object, ...]]] = []

        def probe_obd(port: str, baud: int, timeout: float) -> DiagnosticResult:
            calls.append(("obd", (port, baud, timeout)))
            return DiagnosticResult("obd", True, "ELM OK")

        def probe_can(channel: str, timeout: float) -> DiagnosticResult:
            calls.append(("can", (channel, timeout)))
            return DiagnosticResult("can", False, "no frames")

        result = probe_input_status(
            {"configured": True, "transport": "serial", "port": "/dev/rfcomm0", "baud": 38400},
            {"configured": True, "channel": "can0"},
            enabled=True,
            obd_timeout=1.5,
            can_timeout=2.5,
            probe_obd_func=probe_obd,
            probe_can_func=probe_can,
        )

        self.assertEqual([("obd", ("/dev/rfcomm0", 38400, 1.5)), ("can", ("can0", 2.5))], calls)
        self.assertTrue(result["obd"]["ok"])
        self.assertFalse(result["can"]["ok"])
        self.assertEqual(["CAN live probe failed: no frames"], result["issues"])

    def test_display_probe_status_uses_injected_display_probe_function(self) -> None:
        result = display_probe_status(
            1920,
            480,
            enabled=True,
            probe_display_func=lambda width, height: DiagnosticResult("display", False, f"{width}x{height} wrong"),
        )

        self.assertFalse(result["ok"])
        self.assertEqual("display", result["name"])
        self.assertEqual(["display probe failed: 1920x480 wrong"], result["issues"])


if __name__ == "__main__":
    unittest.main()
