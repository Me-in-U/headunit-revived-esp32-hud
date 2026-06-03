from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


def load_acceptance_check_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "acceptance-check.py"
    spec = importlib.util.spec_from_file_location("acceptance_check", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load acceptance-check.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AcceptanceCheckScriptTest(unittest.TestCase):
    def test_report_marks_ready_for_car_without_android_bridge_when_pi_inputs_are_configured(self) -> None:
        module = load_acceptance_check_module()

        report = module.build_acceptance_report(
            {
                "HEADUNIT_HUD_LAYOUT": "layouts/avante_hd_2010_default.json",
                "HEADUNIT_HUD_WIDTH": "1920",
                "HEADUNIT_HUD_HEIGHT": "480",
                "HEADUNIT_HUD_DUMMY": "0",
                "HEADUNIT_HUD_OBD_PORT": "/dev/rfcomm0",
                "HEADUNIT_HUD_CAN_CHANNEL": "can0",
                "HEADUNIT_HUD_DISABLE_DISCOVERY": "1",
            }
        )

        acceptance = report["acceptance"]
        self.assertTrue(acceptance["layout_ready"])
        self.assertTrue(acceptance["display_ready"])
        self.assertTrue(acceptance["standalone_ready"])
        self.assertTrue(acceptance["bridge_optional"])
        self.assertTrue(acceptance["pi_vehicle_inputs_configured"])
        self.assertTrue(acceptance["vehicle_profile_ready"])
        self.assertFalse(acceptance["live_input_ready"])
        self.assertTrue(acceptance["ready_for_car"])
        self.assertFalse(report["first_run"]["android_bridge"]["required_for_standalone"])

    def test_report_checks_installed_vehicle_profile_for_selected_layout_vehicle(self) -> None:
        module = load_acceptance_check_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            app_dir = Path(temp_dir) / "app"
            vehicles_dir = app_dir / "vehicles"
            vehicles_dir.mkdir(parents=True)
            profile = json.loads(Path("vehicles/avante_hd_2010_1_6_at.json").read_text(encoding="utf-8"))
            (vehicles_dir / "avante_hd_2010_1_6_at.json").write_text(json.dumps(profile), encoding="utf-8")

            report = module.build_acceptance_report(
                {
                    "HEADUNIT_HUD_APP_DIR": str(app_dir),
                    "HEADUNIT_HUD_LAYOUT": "layouts/avante_hd_2010_default.json",
                    "HEADUNIT_HUD_WIDTH": "1920",
                    "HEADUNIT_HUD_HEIGHT": "480",
                    "HEADUNIT_HUD_DUMMY": "0",
                    "HEADUNIT_HUD_OBD_PORT": "/dev/rfcomm0",
                    "HEADUNIT_HUD_CAN_CHANNEL": "can0",
                }
            )

        self.assertTrue(report["acceptance"]["vehicle_profile_ready"])
        self.assertEqual("avante_hd_2010_1_6_at", report["vehicle_profile"]["selected_vehicle"])
        self.assertEqual(str(vehicles_dir / "avante_hd_2010_1_6_at.json"), report["vehicle_profile"]["path"])

    def test_report_uses_actual_vehicle_profile_file_path_when_filename_differs_from_id(self) -> None:
        module = load_acceptance_check_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            app_dir = Path(temp_dir) / "app"
            vehicles_dir = app_dir / "vehicles"
            vehicles_dir.mkdir(parents=True)
            profile = json.loads(Path("vehicles/avante_hd_2010_1_6_at.json").read_text(encoding="utf-8"))
            installed_profile_path = vehicles_dir / "current-car.json"
            installed_profile_path.write_text(json.dumps(profile), encoding="utf-8")

            report = module.build_acceptance_report(
                {
                    "HEADUNIT_HUD_APP_DIR": str(app_dir),
                    "HEADUNIT_HUD_LAYOUT": "layouts/avante_hd_2010_default.json",
                    "HEADUNIT_HUD_WIDTH": "1920",
                    "HEADUNIT_HUD_HEIGHT": "480",
                    "HEADUNIT_HUD_DUMMY": "0",
                    "HEADUNIT_HUD_OBD_PORT": "/dev/rfcomm0",
                    "HEADUNIT_HUD_CAN_CHANNEL": "can0",
                }
            )

        self.assertTrue(report["acceptance"]["vehicle_profile_ready"])
        self.assertEqual(str(installed_profile_path), report["vehicle_profile"]["path"])

    def test_report_blocks_ready_for_car_when_selected_vehicle_profile_is_missing_from_app_vehicles_dir(self) -> None:
        module = load_acceptance_check_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            app_dir = Path(temp_dir) / "app"
            (app_dir / "vehicles").mkdir(parents=True)

            report = module.build_acceptance_report(
                {
                    "HEADUNIT_HUD_APP_DIR": str(app_dir),
                    "HEADUNIT_HUD_LAYOUT": "layouts/avante_hd_2010_default.json",
                    "HEADUNIT_HUD_WIDTH": "1920",
                    "HEADUNIT_HUD_HEIGHT": "480",
                    "HEADUNIT_HUD_DUMMY": "0",
                    "HEADUNIT_HUD_OBD_PORT": "/dev/rfcomm0",
                    "HEADUNIT_HUD_CAN_CHANNEL": "can0",
                }
            )

        acceptance = report["acceptance"]
        self.assertFalse(acceptance["vehicle_profile_ready"])
        self.assertFalse(acceptance["ready_for_car"])
        self.assertIn("selected vehicle profile is not installed: avante_hd_2010_1_6_at", acceptance["issues"])

    def test_report_requires_live_inputs_only_when_probe_inputs_is_requested(self) -> None:
        module = load_acceptance_check_module()

        with patch("hud_pi.first_run.probe_obd", return_value=module.DiagnosticResult("obd", False, "no ELM")), patch(
            "hud_pi.first_run.probe_can", return_value=module.DiagnosticResult("can", True, "frames=3")
        ):
            report = module.build_acceptance_report(
                {
                    "HEADUNIT_HUD_LAYOUT": "layouts/avante_hd_2010_default.json",
                    "HEADUNIT_HUD_WIDTH": "1920",
                    "HEADUNIT_HUD_HEIGHT": "480",
                    "HEADUNIT_HUD_DUMMY": "0",
                    "HEADUNIT_HUD_OBD_PORT": "/dev/rfcomm0",
                    "HEADUNIT_HUD_CAN_CHANNEL": "can0",
                },
                probe_inputs=True,
            )

        acceptance = report["acceptance"]
        self.assertFalse(acceptance["live_input_ready"])
        self.assertFalse(acceptance["ready_for_car"])
        self.assertIn("OBD live probe failed: no ELM", acceptance["issues"])

    def test_main_loads_env_file_writes_json_and_returns_ready_exit_code_without_hardware_probes(self) -> None:
        module = load_acceptance_check_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / "headunit-pi-hud.env"
            output = Path(temp_dir) / "acceptance-check.json"
            env_file.write_text(
                "\n".join(
                    [
                        "HEADUNIT_HUD_LAYOUT=layouts/avante_hd_2010_default.json",
                        "HEADUNIT_HUD_WIDTH=1920",
                        "HEADUNIT_HUD_HEIGHT=480",
                        "HEADUNIT_HUD_DUMMY=0",
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
                exit_code = module.main(["--output", str(output), "--json"])

            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(0, exit_code)
        self.assertTrue(payload["acceptance"]["ready_for_car"])
        self.assertEqual("layouts/avante_hd_2010_default.json", payload["first_run"]["layout"]["path"])

    def test_parser_can_force_layout_handoff_requirement(self) -> None:
        module = load_acceptance_check_module()

        args = module.build_parser().parse_args(["--require-handoff", "--probe-display", "--probe-inputs"])

        self.assertTrue(args.require_handoff)
        self.assertTrue(args.probe_display)
        self.assertTrue(args.probe_inputs)

    def test_format_report_includes_vehicle_profile_status(self) -> None:
        module = load_acceptance_check_module()

        report = module.build_acceptance_report(
            {
                "HEADUNIT_HUD_LAYOUT": "layouts/avante_hd_2010_default.json",
                "HEADUNIT_HUD_WIDTH": "1920",
                "HEADUNIT_HUD_HEIGHT": "480",
                "HEADUNIT_HUD_DUMMY": "0",
                "HEADUNIT_HUD_OBD_PORT": "/dev/rfcomm0",
                "HEADUNIT_HUD_CAN_CHANNEL": "can0",
            }
        )

        formatted = module.format_report(report)

        self.assertIn("Vehicle profile: OK (avante_hd_2010_1_6_at)", formatted)


if __name__ == "__main__":
    unittest.main()
