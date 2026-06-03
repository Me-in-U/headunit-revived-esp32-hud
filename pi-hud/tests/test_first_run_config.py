from __future__ import annotations

import unittest

from hud_pi.first_run_config import bridge_status, can_status, env_int, env_truthy, next_steps, obd_status


class FirstRunConfigTest(unittest.TestCase):
    def test_env_helpers_and_input_statuses_preserve_first_run_configuration_contract(self) -> None:
        environ = {
            "HEADUNIT_HUD_OBD_PORT": "/dev/rfcomm0",
            "HEADUNIT_HUD_OBD_BAUD": "bad",
            "HEADUNIT_HUD_CAN_CHANNEL": "can0",
            "HEADUNIT_HUD_CAN_BITRATE": "500000",
            "HEADUNIT_HUD_CAN_LISTEN_ONLY": "off",
            "HEADUNIT_HUD_UDP_PORT": "4210",
            "HEADUNIT_HUD_DISCOVERY_PORT": "4211",
            "HEADUNIT_HUD_DISABLE_DISCOVERY": "yes",
        }

        self.assertTrue(env_truthy("ON"))
        self.assertFalse(env_truthy("0"))
        self.assertEqual(38400, env_int(environ, "HEADUNIT_HUD_OBD_BAUD", 38400))
        self.assertEqual(
            {"configured": True, "transport": "serial", "port": "/dev/rfcomm0", "baud": 38400, "issue": ""},
            obd_status(environ),
        )
        self.assertEqual(
            {"configured": True, "channel": "can0", "bitrate": 500000, "listen_only": "off", "issue": ""},
            can_status(environ),
        )
        self.assertEqual(
            {
                "role": "navigation_and_backup_speed_only",
                "required_for_standalone": False,
                "udp_port": 4210,
                "discovery_port": 4211,
                "discovery_enabled": False,
            },
            bridge_status(environ),
        )

    def test_next_steps_prioritize_dummy_missing_inputs_and_probe_failures(self) -> None:
        steps = next_steps(
            {"configured": False, "transport": "ble"},
            {"configured": False},
            dummy_enabled=True,
            probe_inputs=True,
            input_probe_issues=["OBD live probe failed: no data"],
            probe_display_output=True,
            display_probe_issues=["display probe failed: wrong mode"],
        )

        self.assertEqual(
            [
                "Set HEADUNIT_HUD_DUMMY=0 for real Pi standalone use.",
                "Fill HEADUNIT_HUD_OBD_BLE_RX_UUID and HEADUNIT_HUD_OBD_BLE_TX_UUID, then run diagnose-inputs.py.",
                "Set HEADUNIT_HUD_CAN_CHANNEL=can0 and bring CANable up in listen-only mode.",
                "Fix live OBD/CAN probe failures before relying on real vehicle data.",
                "Fix the Pi framebuffer/display mode before relying on the 1920x480 HUD.",
            ],
            steps,
        )


if __name__ == "__main__":
    unittest.main()
