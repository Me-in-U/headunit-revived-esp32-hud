from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import json


def load_collect_vehicle_baseline_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "collect-vehicle-baseline.py"
    spec = importlib.util.spec_from_file_location("collect_vehicle_baseline", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load collect-vehicle-baseline.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CollectVehicleBaselineScriptTest(unittest.TestCase):
    def test_runtime_environment_file_is_loaded_before_parser_defaults(self) -> None:
        module = load_collect_vehicle_baseline_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / "headunit-pi-hud.env"
            env_file.write_text(
                "\n".join(
                    [
                        "HEADUNIT_HUD_OBD_PORT=/dev/rfcomm0",
                        "HEADUNIT_HUD_OBD_BAUD=115200",
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

        self.assertEqual("/dev/rfcomm0", args.obd_port)
        self.assertEqual(115200, args.obd_baud)

    def test_ble_obd_environment_is_loaded_before_parser_defaults(self) -> None:
        module = load_collect_vehicle_baseline_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / "headunit-pi-hud.env"
            env_file.write_text(
                "\n".join(
                    [
                        "HEADUNIT_HUD_OBD_BLE_MAC=AA:BB:CC:DD:EE:FF",
                        "HEADUNIT_HUD_OBD_BLE_RX_UUID=0000fff1-0000-1000-8000-00805f9b34fb",
                        "HEADUNIT_HUD_OBD_BLE_TX_UUID=0000fff2-0000-1000-8000-00805f9b34fb",
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

        self.assertEqual("AA:BB:CC:DD:EE:FF", args.obd_ble_mac)
        self.assertEqual("0000fff1-0000-1000-8000-00805f9b34fb", args.obd_ble_rx_uuid)
        self.assertEqual("0000fff2-0000-1000-8000-00805f9b34fb", args.obd_ble_tx_uuid)

    def test_collect_obd_uses_ble_transport_when_serial_port_is_not_configured(self) -> None:
        module = load_collect_vehicle_baseline_module()
        args = module.build_parser().parse_args(
            [
                "--obd-ble-mac",
                "AA:BB:CC:DD:EE:FF",
                "--obd-ble-rx-uuid",
                "rx",
                "--obd-ble-tx-uuid",
                "tx",
            ]
        )

        with patch.object(module, "collect_obd_ble_baseline", return_value=[{"command": "ATI", "response": "ELM327", "ok": True}]):
            result = module.collect_obd(args)

        self.assertTrue(result["configured"])
        self.assertEqual("ble", result["transport"])
        self.assertEqual("AA:BB:CC:DD:EE:FF", result["mac"])
        self.assertEqual([{"command": "ATI", "response": "ELM327", "ok": True}], result["records"])

    def test_build_obd_commands_appends_vehicle_profile_probe_commands(self) -> None:
        module = load_collect_vehicle_baseline_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            profile_path = Path(temp_dir) / "vehicle.json"
            profile_path.write_text(
                json.dumps(
                    {
                        "id": "test_vehicle",
                        "label": "Test Vehicle",
                        "obd_probe_commands": [{"commands": ["ATSH7E0", "ATCRA7E8", "2101"]}],
                    }
                ),
                encoding="utf-8",
            )
            args = module.build_parser().parse_args(["--vehicle-profile", str(profile_path)])

            commands = module.build_obd_commands(args)

        self.assertIn("010C", commands)
        self.assertEqual(["ATSH7E0", "ATCRA7E8", "2101"], commands[-3:])

    def test_build_report_passes_profile_obd_commands_to_obd_collector(self) -> None:
        module = load_collect_vehicle_baseline_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            profile_path = Path(temp_dir) / "vehicle.json"
            profile_path.write_text(
                json.dumps(
                    {
                        "id": "test_vehicle",
                        "label": "Test Vehicle",
                        "obd_probe_commands": [{"commands": ["ATSH7D1", "ATCRA7D9", "220104"]}],
                    }
                ),
                encoding="utf-8",
            )
            args = module.build_parser().parse_args(["--vehicle-profile", str(profile_path)])

            with patch.object(module, "collect_obd", return_value={"configured": False, "records": []}) as collect_obd:
                report = module.build_report(args)

        self.assertEqual("test_vehicle", report["vehicle"])
        self.assertNotIn("can", report)
        collect_obd.assert_called_once()
        self.assertEqual(["ATSH7D1", "ATCRA7D9", "220104"], collect_obd.call_args.args[1][-3:])


if __name__ == "__main__":
    unittest.main()
