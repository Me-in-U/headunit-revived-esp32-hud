from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


def load_diagnose_inputs_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "diagnose-inputs.py"
    spec = importlib.util.spec_from_file_location("diagnose_inputs", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load diagnose-inputs.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DiagnoseInputsScriptTest(unittest.TestCase):
    def test_runtime_environment_file_is_loaded_before_parser_defaults(self) -> None:
        module = load_diagnose_inputs_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / "headunit-pi-hud.env"
            env_file.write_text(
                "\n".join(
                    [
                        "HEADUNIT_HUD_OBD_PORT=/dev/rfcomm0",
                        "HEADUNIT_HUD_OBD_BAUD=115200",
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

        self.assertEqual("/dev/rfcomm0", args.obd_port)
        self.assertEqual(115200, args.obd_baud)
        self.assertEqual("can0", args.can_channel)

    def test_ble_obd_environment_is_loaded_before_parser_defaults(self) -> None:
        module = load_diagnose_inputs_module()
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


if __name__ == "__main__":
    unittest.main()
