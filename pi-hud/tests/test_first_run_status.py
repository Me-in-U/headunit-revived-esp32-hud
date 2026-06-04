from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from hud_pi.diagnostics import DiagnosticResult
from hud_pi.first_run import build_first_run_report


def load_first_run_status_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "first-run-status.py"
    spec = importlib.util.spec_from_file_location("first_run_status", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load first-run-status.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FirstRunStatusTest(unittest.TestCase):
    def test_report_marks_pi_standalone_ready_with_serial_obd_and_canable_configured(self) -> None:
        report = build_first_run_report(
            {
                "HEADUNIT_HUD_LAYOUT": "layouts/avante_hd_2010_default.json",
                "HEADUNIT_HUD_WIDTH": "1920",
                "HEADUNIT_HUD_HEIGHT": "480",
                "HEADUNIT_HUD_DUMMY": "0",
                "HEADUNIT_HUD_OBD_PORT": "/dev/rfcomm0",
                "HEADUNIT_HUD_OBD_BAUD": "38400",
                "HEADUNIT_HUD_CAN_CHANNEL": "can0",
                "HEADUNIT_HUD_CAN_BITRATE": "500000",
                "HEADUNIT_HUD_CAN_LISTEN_ONLY": "on",
                "HEADUNIT_HUD_UDP_PORT": "4210",
                "HEADUNIT_HUD_DISCOVERY_PORT": "4211",
            }
        )

        self.assertTrue(report["standalone_ready"])
        self.assertEqual("serial", report["obd"]["transport"])
        self.assertTrue(report["obd"]["configured"])
        self.assertTrue(report["can"]["configured"])
        self.assertEqual("navigation_and_backup_speed_only", report["android_bridge"]["role"])
        self.assertEqual([], report["blocking_issues"])

    def test_report_blocks_standalone_ready_when_ble_uuid_config_is_incomplete(self) -> None:
        report = build_first_run_report(
            {
                "HEADUNIT_HUD_LAYOUT": "layouts/avante_hd_2010_default.json",
                "HEADUNIT_HUD_DUMMY": "0",
                "HEADUNIT_HUD_OBD_PORT": "",
                "HEADUNIT_HUD_OBD_BLE_MAC": "AA:BB:CC:DD:EE:FF",
                "HEADUNIT_HUD_OBD_BLE_RX_UUID": "",
                "HEADUNIT_HUD_OBD_BLE_TX_UUID": "",
                "HEADUNIT_HUD_CAN_CHANNEL": "can0",
            }
        )

        self.assertFalse(report["standalone_ready"])
        self.assertEqual("ble", report["obd"]["transport"])
        self.assertFalse(report["obd"]["configured"])
        self.assertIn("OBD BLE RX/TX UUID is missing", report["blocking_issues"])

    def test_report_blocks_standalone_ready_when_dummy_is_forced(self) -> None:
        report = build_first_run_report(
            {
                "HEADUNIT_HUD_LAYOUT": "layouts/avante_hd_2010_default.json",
                "HEADUNIT_HUD_DUMMY": "1",
                "HEADUNIT_HUD_OBD_PORT": "/dev/rfcomm0",
                "HEADUNIT_HUD_CAN_CHANNEL": "can0",
            }
        )

        self.assertFalse(report["standalone_ready"])
        self.assertIn("dummy mode is enabled", report["blocking_issues"])

    def test_report_blocks_standalone_ready_when_layout_handoff_is_required_but_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            layout_path = Path(temp_dir) / "missing-handoff.json"
            layout = json.loads(Path("layouts/avante_hd_2010_default.json").read_text(encoding="utf-8"))
            layout.pop("pi_hud_handoff", None)
            layout_path.write_text(json.dumps(layout, ensure_ascii=False), encoding="utf-8")

            report = build_first_run_report(
                {
                    "HEADUNIT_HUD_LAYOUT": str(layout_path),
                    "HEADUNIT_HUD_REQUIRE_HANDOFF": "1",
                    "HEADUNIT_HUD_DUMMY": "0",
                    "HEADUNIT_HUD_OBD_PORT": "/dev/rfcomm0",
                    "HEADUNIT_HUD_CAN_CHANNEL": "can0",
                }
            )

        self.assertFalse(report["standalone_ready"])
        self.assertIn("layout is not valid: pi_hud_handoff metadata is missing", report["blocking_issues"])
        self.assertTrue(report["layout"]["require_handoff"])

    def test_script_loads_env_file_before_parser_defaults(self) -> None:
        module = load_first_run_status_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / "headunit-pi-hud.env"
            env_file.write_text(
                "\n".join(
                    [
                        "HEADUNIT_HUD_LAYOUT=layouts/avante_hd_2010_default.json",
                        "HEADUNIT_HUD_OBD_PORT=/dev/rfcomm0",
                        "HEADUNIT_HUD_CAN_CHANNEL=can0",
                    ]
                ),
                encoding="utf-8",
            )
            clean_env = {
                key: value
                for key, value in os.environ.items()
                if not key.startswith("HEADUNIT_HUD_")
            }
            clean_env["HEADUNIT_HUD_ENV_FILE"] = str(env_file)

            with patch.dict(os.environ, clean_env, clear=True):
                module.load_runtime_environment()
                args = module.build_parser().parse_args([])

        self.assertEqual("layouts/avante_hd_2010_default.json", args.layout)

    def test_script_loads_screen_test_env_override_after_persistent_env(self) -> None:
        module = load_first_run_status_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / "headunit-pi-hud.env"
            test_env_file = Path(temp_dir) / "headunit-pi-hud-test.env"
            env_file.write_text(
                "\n".join(
                    [
                        "HEADUNIT_HUD_WIDTH=1920",
                        "HEADUNIT_HUD_HEIGHT=480",
                        "HEADUNIT_HUD_DUMMY=0",
                        "HEADUNIT_HUD_REQUIRE_HANDOFF=1",
                    ]
                ),
                encoding="utf-8",
            )
            test_env_file.write_text(
                "\n".join(
                    [
                        "HEADUNIT_HUD_WIDTH=1280",
                        "HEADUNIT_HUD_HEIGHT=720",
                        "HEADUNIT_HUD_DUMMY=1",
                        "HEADUNIT_HUD_REQUIRE_HANDOFF=0",
                    ]
                ),
                encoding="utf-8",
            )
            clean_env = {
                key: value
                for key, value in os.environ.items()
                if not key.startswith("HEADUNIT_HUD_")
            }
            clean_env["HEADUNIT_HUD_ENV_FILE"] = str(env_file)
            clean_env["HEADUNIT_HUD_TEST_ENV_FILE"] = str(test_env_file)

            with patch.dict(os.environ, clean_env, clear=True):
                loaded = module.load_runtime_environment()
                width = os.environ["HEADUNIT_HUD_WIDTH"]
                height = os.environ["HEADUNIT_HUD_HEIGHT"]
                dummy = os.environ["HEADUNIT_HUD_DUMMY"]
                require_handoff = os.environ["HEADUNIT_HUD_REQUIRE_HANDOFF"]

        self.assertIn("HEADUNIT_HUD_WIDTH", loaded)
        self.assertEqual("1280", width)
        self.assertEqual("720", height)
        self.assertEqual("1", dummy)
        self.assertEqual("0", require_handoff)

    def test_report_runs_live_obd_and_can_probes_when_requested(self) -> None:
        environ = {
            "HEADUNIT_HUD_LAYOUT": "layouts/avante_hd_2010_default.json",
            "HEADUNIT_HUD_DUMMY": "0",
            "HEADUNIT_HUD_OBD_PORT": "/dev/rfcomm0",
            "HEADUNIT_HUD_OBD_BAUD": "38400",
            "HEADUNIT_HUD_CAN_CHANNEL": "can0",
        }
        with patch("hud_pi.first_run.probe_obd", return_value=DiagnosticResult("obd", True, "ELM OK")) as probe_obd, patch(
            "hud_pi.first_run.probe_can", return_value=DiagnosticResult("can", True, "frames=4")
        ) as probe_can:
            report = build_first_run_report(environ, probe_inputs=True, obd_timeout=1.5, can_timeout=2.5)

        self.assertTrue(report["input_probes"]["enabled"])
        self.assertTrue(report["input_probes"]["obd"]["ok"])
        self.assertTrue(report["input_probes"]["can"]["ok"])
        self.assertTrue(report["live_input_ready"])
        probe_obd.assert_called_once_with("/dev/rfcomm0", 38400, 1.5)
        probe_can.assert_called_once_with("can0", 2.5)

    def test_report_marks_live_input_not_ready_when_probe_fails(self) -> None:
        environ = {
            "HEADUNIT_HUD_LAYOUT": "layouts/avante_hd_2010_default.json",
            "HEADUNIT_HUD_DUMMY": "0",
            "HEADUNIT_HUD_OBD_PORT": "/dev/rfcomm0",
            "HEADUNIT_HUD_CAN_CHANNEL": "can0",
        }
        with patch("hud_pi.first_run.probe_obd", return_value=DiagnosticResult("obd", False, "no data")), patch(
            "hud_pi.first_run.probe_can", return_value=DiagnosticResult("can", True, "frames=4")
        ):
            report = build_first_run_report(environ, probe_inputs=True)

        self.assertTrue(report["standalone_ready"])
        self.assertFalse(report["live_input_ready"])
        self.assertIn("OBD live probe failed: no data", report["probe_issues"])

    def test_report_runs_display_probe_when_requested(self) -> None:
        environ = {
            "HEADUNIT_HUD_LAYOUT": "layouts/avante_hd_2010_default.json",
            "HEADUNIT_HUD_DUMMY": "0",
            "HEADUNIT_HUD_OBD_PORT": "/dev/rfcomm0",
            "HEADUNIT_HUD_CAN_CHANNEL": "can0",
        }
        with patch("hud_pi.first_run.probe_display", return_value=DiagnosticResult("display", True, "framebuffer=1920x480")) as display_probe:
            report = build_first_run_report(environ, probe_display_output=True)

        self.assertTrue(report["display"]["probe"]["enabled"])
        self.assertTrue(report["display"]["probe"]["ok"])
        self.assertTrue(report["display_ready"])
        display_probe.assert_called_once_with(1920, 480)

    def test_report_marks_display_not_ready_when_probe_fails(self) -> None:
        environ = {
            "HEADUNIT_HUD_LAYOUT": "layouts/avante_hd_2010_default.json",
            "HEADUNIT_HUD_DUMMY": "0",
            "HEADUNIT_HUD_OBD_PORT": "/dev/rfcomm0",
            "HEADUNIT_HUD_CAN_CHANNEL": "can0",
        }
        with patch(
            "hud_pi.first_run.probe_display",
            return_value=DiagnosticResult("display", False, "framebuffer=1280x720, expected 1920x480"),
        ):
            report = build_first_run_report(environ, probe_display_output=True)

        self.assertTrue(report["standalone_ready"])
        self.assertFalse(report["display_ready"])
        self.assertIn("display probe failed: framebuffer=1280x720, expected 1920x480", report["probe_issues"])

    def test_script_parser_accepts_probe_inputs_option(self) -> None:
        module = load_first_run_status_module()

        args = module.build_parser().parse_args(["--probe-inputs", "--obd-timeout", "1.5", "--can-timeout", "2.5"])

        self.assertTrue(args.probe_inputs)
        self.assertEqual(1.5, args.obd_timeout)
        self.assertEqual(2.5, args.can_timeout)

    def test_script_parser_accepts_probe_display_option(self) -> None:
        module = load_first_run_status_module()

        args = module.build_parser().parse_args(["--probe-display"])

        self.assertTrue(args.probe_display)


if __name__ == "__main__":
    unittest.main()
