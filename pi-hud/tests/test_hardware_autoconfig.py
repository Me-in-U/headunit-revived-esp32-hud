from __future__ import annotations

import unittest

from hud_pi.diagnostics_common import DiagnosticResult
from hud_pi.hardware_autoconfig import (
    BleObdPair,
    BluetoothDevice,
    auto_configure_hardware,
    merge_env_updates,
    parse_bluetoothctl_devices,
    parse_can_channels,
    select_obd_candidate,
)


class HardwareAutoConfigTest(unittest.TestCase):
    def test_parse_and_select_single_obd_bluetooth_candidate(self) -> None:
        devices = parse_bluetoothctl_devices(
            "\n".join(
                [
                    "Device AA:BB:CC:DD:EE:FF V-LINK",
                    "Device 11:22:33:44:55:66 Keyboard",
                    "Device 22:33:44:55:66:77 iPhone",
                ]
            )
        )

        candidate = select_obd_candidate(devices)

        self.assertEqual(BluetoothDevice("AA:BB:CC:DD:EE:FF", "V-LINK"), candidate)

    def test_select_obd_candidate_refuses_ambiguous_bluetooth_devices(self) -> None:
        candidate = select_obd_candidate(
            [
                BluetoothDevice("AA:BB:CC:DD:EE:FF", "V-LINK"),
                BluetoothDevice("BB:CC:DD:EE:FF:00", "ELM327"),
            ]
        )

        self.assertIsNone(candidate)

    def test_parse_can_channels_prefers_can0(self) -> None:
        channels = parse_can_channels(
            "\n".join(
                [
                    "1: lo: <LOOPBACK,UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000",
                    "2: can1: <NOARP,ECHO> mtu 16 qdisc noop state DOWN mode DEFAULT group default qlen 10",
                    "3: can0: <NOARP,ECHO> mtu 16 qdisc noop state DOWN mode DEFAULT group default qlen 10",
                ]
            )
        )

        self.assertEqual(["can0", "can1"], channels)

    def test_merge_env_updates_preserves_comments_and_appends_missing_keys(self) -> None:
        env_text = "\n".join(
            [
                "# Runtime",
                "HEADUNIT_HUD_AUTO_UPDATE=0",
                "HEADUNIT_HUD_OBD_PORT=/dev/rfcomm0",
                "",
            ]
        )

        updated = merge_env_updates(
            env_text,
            {
                "HEADUNIT_HUD_AUTO_UPDATE": "1",
                "HEADUNIT_HUD_OBD_PORT": "",
                "HEADUNIT_HUD_ICAR_MAC": "AA:BB:CC:DD:EE:FF",
            },
        )

        self.assertIn("# Runtime\n", updated)
        self.assertIn("HEADUNIT_HUD_AUTO_UPDATE=1\n", updated)
        self.assertIn("HEADUNIT_HUD_OBD_PORT=\n", updated)
        self.assertTrue(updated.endswith("HEADUNIT_HUD_ICAR_MAC=AA:BB:CC:DD:EE:FF\n"))

    def test_auto_configure_hardware_sets_serial_obd_and_can_when_probes_pass(self) -> None:
        result = auto_configure_hardware(
            {},
            bluetooth_devices=[BluetoothDevice("AA:BB:CC:DD:EE:FF", "V-LINK")],
            can_channels=["can0"],
            rfcomm_bind=lambda mac, index, channel: f"/dev/rfcomm{index}",
            probe_serial_obd=lambda port, baud: DiagnosticResult("obd", True, f"{port} ok"),
            discover_ble_obd=lambda mac: [],
            probe_ble_obd=lambda mac, rx_uuid, tx_uuid: DiagnosticResult("obd-ble", False, "not used"),
            setup_can=lambda channel, bitrate, listen_only: None,
            probe_can_channel=lambda channel: DiagnosticResult("can", True, f"{channel} frames=3"),
        )

        self.assertEqual(
            {
                "HEADUNIT_HUD_OBD_PORT": "/dev/rfcomm0",
                "HEADUNIT_HUD_ICAR_MAC": "AA:BB:CC:DD:EE:FF",
                "HEADUNIT_HUD_RFCOMM_INDEX": "0",
                "HEADUNIT_HUD_RFCOMM_CHANNEL": "1",
                "HEADUNIT_HUD_CAN_CHANNEL": "can0",
                "HEADUNIT_HUD_CAN_BITRATE": "500000",
                "HEADUNIT_HUD_CAN_LISTEN_ONLY": "on",
            },
            result.updates,
        )
        self.assertEqual([], result.issues)

    def test_auto_configure_hardware_falls_back_to_ble_pair_when_rfcomm_fails(self) -> None:
        result = auto_configure_hardware(
            {},
            bluetooth_devices=[BluetoothDevice("AA:BB:CC:DD:EE:FF", "iCar Pro")],
            can_channels=[],
            rfcomm_bind=lambda mac, index, channel: "/dev/rfcomm0",
            probe_serial_obd=lambda port, baud: DiagnosticResult("obd", False, "rfcomm failed"),
            discover_ble_obd=lambda mac: [BleObdPair("rx-uuid", "tx-uuid")],
            probe_ble_obd=lambda mac, rx_uuid, tx_uuid: DiagnosticResult("obd-ble", True, "ble ok"),
            setup_can=lambda channel, bitrate, listen_only: None,
            probe_can_channel=lambda channel: DiagnosticResult("can", False, "not used"),
        )

        self.assertEqual(
            {
                "HEADUNIT_HUD_OBD_PORT": "",
                "HEADUNIT_HUD_OBD_BLE_MAC": "AA:BB:CC:DD:EE:FF",
                "HEADUNIT_HUD_OBD_BLE_RX_UUID": "rx-uuid",
                "HEADUNIT_HUD_OBD_BLE_TX_UUID": "tx-uuid",
            },
            result.updates,
        )
        self.assertIn("CANable SocketCAN channel was not found", result.issues)


if __name__ == "__main__":
    unittest.main()
