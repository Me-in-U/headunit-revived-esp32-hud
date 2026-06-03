from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from hud_pi.diagnostics_common import DiagnosticResult, compact_response, format_result, load_env_file
from hud_pi.diagnostics_display import parse_framebuffer_virtual_size, probe_display


class DiagnosticsCommonTest(unittest.TestCase):
    def test_common_helpers_format_results_compact_responses_and_load_env_values(self) -> None:
        env = {"HEADUNIT_HUD_OBD_PORT": "/dev/user-obd"}
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / "headunit-pi-hud.env"
            env_path.write_text(
                "\n".join(
                    [
                        "# copied from /etc/headunit-pi-hud.env",
                        "HEADUNIT_HUD_OBD_PORT=/dev/rfcomm0",
                        "export HEADUNIT_HUD_CAN_CHANNEL=can0",
                        'HEADUNIT_HUD_LAYOUT="/opt/headunit-pi-hud/layouts/default.json"',
                    ]
                ),
                encoding="utf-8",
            )

            loaded = load_env_file(env_path, env)

        self.assertEqual(["HEADUNIT_HUD_CAN_CHANNEL", "HEADUNIT_HUD_LAYOUT"], loaded)
        self.assertEqual("/dev/user-obd", env["HEADUNIT_HUD_OBD_PORT"])
        self.assertEqual("can0", env["HEADUNIT_HUD_CAN_CHANNEL"])
        self.assertEqual("/opt/headunit-pi-hud/layouts/default.json", env["HEADUNIT_HUD_LAYOUT"])
        self.assertEqual("ELM327 v1.5 41 00 BE 1F A8 13", compact_response("ELM327 v1.5\n\n41 00 BE 1F A8 13\n"))
        self.assertEqual("[FAIL] can: no frames", format_result(DiagnosticResult("can", False, "no frames")))

    def test_display_helpers_parse_and_probe_framebuffer_virtual_size(self) -> None:
        self.assertEqual((1920, 480), parse_framebuffer_virtual_size("1920,480\n"))
        self.assertEqual((1920, 480), parse_framebuffer_virtual_size("1920x480"))

        with tempfile.TemporaryDirectory() as temp_dir:
            fb_path = Path(temp_dir) / "virtual_size"
            fb_path.write_text("1280,720\n", encoding="utf-8")

            result = probe_display(1920, 480, fb_path)

        self.assertFalse(result.ok)
        self.assertEqual("display", result.name)
        self.assertEqual("framebuffer=1280x720, expected 1920x480", result.detail)


if __name__ == "__main__":
    unittest.main()
