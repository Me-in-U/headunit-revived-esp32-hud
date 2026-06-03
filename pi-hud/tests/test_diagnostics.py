from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from hud_pi.diagnostics import (
    DiagnosticResult,
    compact_response,
    format_result,
    layout_summary,
    load_env_file,
    probe_display,
    probe_obd_ble,
)


class DiagnosticsTest(unittest.TestCase):
    def test_layout_summary_reports_default_vehicle_and_size(self) -> None:
        result = layout_summary("layouts/avante_hd_2010_default.json")

        self.assertTrue(result.ok)
        self.assertIn("1920x480", result.detail)
        self.assertIn("vehicle=avante_hd_2010_1_6_at", result.detail)

    def test_layout_summary_rejects_layout_with_missing_dummy_binding(self) -> None:
        layout = {
            "canvas": {"width": 1920, "height": 480},
            "dummy_data": {"vehicle": {}},
            "elements": [
                {
                    "id": "speed",
                    "type": "value",
                    "binding": "vehicle.speed_kmh",
                    "x": 0,
                    "y": 0,
                    "w": 100,
                    "h": 40,
                    "font_size": 24,
                }
            ],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad-layout.json"
            path.write_text(json.dumps(layout), encoding="utf-8")

            result = layout_summary(path)

        self.assertFalse(result.ok)
        self.assertIn("binding 'vehicle.speed_kmh' has no dummy_data value", result.detail)

    def test_format_result_marks_failures(self) -> None:
        result = DiagnosticResult("can", False, "no frames")

        self.assertEqual("[FAIL] can: no frames", format_result(result))

    def test_compact_response_removes_prompt_line_breaks(self) -> None:
        self.assertEqual("ELM327 v1.5 41 00 BE 1F A8 13", compact_response("ELM327 v1.5\n\n41 00 BE 1F A8 13\n"))

    def test_load_env_file_sets_missing_values_without_overriding_existing_environment(self) -> None:
        env = {
            "HEADUNIT_HUD_OBD_PORT": "/dev/user-obd",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "headunit-pi-hud.env"
            path.write_text(
                "\n".join(
                    [
                        "# copied from /etc/headunit-pi-hud.env",
                        "HEADUNIT_HUD_OBD_PORT=/dev/rfcomm0",
                        "export HEADUNIT_HUD_CAN_CHANNEL=can0",
                        'HEADUNIT_HUD_LAYOUT="/opt/headunit-pi-hud/layouts/avante_hd_2010_default.json"',
                        "HEADUNIT_HUD_EMPTY=",
                    ]
                ),
                encoding="utf-8",
            )

            loaded = load_env_file(path, env)

        self.assertEqual(["HEADUNIT_HUD_CAN_CHANNEL", "HEADUNIT_HUD_LAYOUT", "HEADUNIT_HUD_EMPTY"], loaded)
        self.assertEqual("/dev/user-obd", env["HEADUNIT_HUD_OBD_PORT"])
        self.assertEqual("can0", env["HEADUNIT_HUD_CAN_CHANNEL"])
        self.assertEqual("/opt/headunit-pi-hud/layouts/avante_hd_2010_default.json", env["HEADUNIT_HUD_LAYOUT"])
        self.assertEqual("", env["HEADUNIT_HUD_EMPTY"])

    def test_load_env_file_ignores_missing_file(self) -> None:
        env = {}

        loaded = load_env_file("does-not-exist.env", env)

        self.assertEqual([], loaded)
        self.assertEqual({}, env)

    def test_probe_obd_ble_reports_missing_characteristic_configuration_before_connecting(self) -> None:
        result = probe_obd_ble("AA:BB:CC:DD:EE:FF", "", "")

        self.assertFalse(result.ok)
        self.assertEqual("obd-ble", result.name)
        self.assertIn("missing RX/TX UUID", result.detail)

    def test_probe_display_reads_linux_framebuffer_virtual_size(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fb_path = Path(temp_dir) / "virtual_size"
            fb_path.write_text("1920,480\n", encoding="utf-8")

            result = probe_display(1920, 480, fb_path)

        self.assertTrue(result.ok)
        self.assertEqual("display", result.name)
        self.assertIn("framebuffer=1920x480", result.detail)

    def test_probe_display_reports_framebuffer_size_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fb_path = Path(temp_dir) / "virtual_size"
            fb_path.write_text("1280,720\n", encoding="utf-8")

            result = probe_display(1920, 480, fb_path)

        self.assertFalse(result.ok)
        self.assertIn("framebuffer=1280x720, expected 1920x480", result.detail)


if __name__ == "__main__":
    unittest.main()
