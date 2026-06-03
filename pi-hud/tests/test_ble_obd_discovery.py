from __future__ import annotations

import unittest

from hud_pi.ble_obd_discovery import BleCharacteristicInfo, classify_ble_obd_characteristics, env_lines_for_ble_obd


class BleObdDiscoveryTest(unittest.TestCase):
    def test_classify_ble_obd_characteristics_finds_notify_rx_and_write_tx_candidates(self) -> None:
        characteristics = [
            BleCharacteristicInfo(
                uuid="0000fff1-0000-1000-8000-00805f9b34fb",
                properties=("notify",),
                service_uuid="0000fff0-0000-1000-8000-00805f9b34fb",
            ),
            BleCharacteristicInfo(
                uuid="0000fff2-0000-1000-8000-00805f9b34fb",
                properties=("write-without-response",),
                service_uuid="0000fff0-0000-1000-8000-00805f9b34fb",
            ),
            BleCharacteristicInfo(
                uuid="0000180a-0000-1000-8000-00805f9b34fb",
                properties=("read",),
                service_uuid="0000180a-0000-1000-8000-00805f9b34fb",
            ),
        ]

        result = classify_ble_obd_characteristics(characteristics)

        self.assertEqual(["0000fff1-0000-1000-8000-00805f9b34fb"], [item.uuid for item in result.rx_candidates])
        self.assertEqual(["0000fff2-0000-1000-8000-00805f9b34fb"], [item.uuid for item in result.tx_candidates])
        self.assertEqual(
            [("0000fff1-0000-1000-8000-00805f9b34fb", "0000fff2-0000-1000-8000-00805f9b34fb")],
            [(pair.rx_uuid, pair.tx_uuid) for pair in result.pairs],
        )

    def test_env_lines_for_ble_obd_uses_pi_runtime_variable_names(self) -> None:
        lines = env_lines_for_ble_obd(
            mac="AA:BB:CC:DD:EE:FF",
            rx_uuid="0000fff1-0000-1000-8000-00805f9b34fb",
            tx_uuid="0000fff2-0000-1000-8000-00805f9b34fb",
        )

        self.assertEqual(
            [
                "HEADUNIT_HUD_OBD_PORT=",
                "HEADUNIT_HUD_OBD_BLE_MAC=AA:BB:CC:DD:EE:FF",
                "HEADUNIT_HUD_OBD_BLE_RX_UUID=0000fff1-0000-1000-8000-00805f9b34fb",
                "HEADUNIT_HUD_OBD_BLE_TX_UUID=0000fff2-0000-1000-8000-00805f9b34fb",
            ],
            lines,
        )


if __name__ == "__main__":
    unittest.main()
