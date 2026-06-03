from __future__ import annotations

import asyncio
import unittest

from hud_pi.obd_ble import BleElm327Link, BleElm327ObdSource


class FakeBleClient:
    def __init__(self) -> None:
        self.notify_callback = None
        self.writes: list[tuple[str, bytes, bool]] = []

    async def start_notify(self, _uuid: str, callback) -> None:
        self.notify_callback = callback

    async def write_gatt_char(self, uuid: str, payload: bytes, response: bool) -> None:
        self.writes.append((uuid, payload, response))
        assert self.notify_callback is not None
        self.notify_callback("rx", bytearray(b"41 0D 2A\r>"))


class ObdBleTest(unittest.TestCase):
    def test_ble_source_reports_missing_config_before_connecting(self) -> None:
        updates: list[tuple[str, dict]] = []
        source = BleElm327ObdSource(lambda name, update: updates.append((name, update)), "", "", "")

        source.run()

        self.assertEqual([("obd", {"vehicle": {"obd_state": "ble-config-missing"}})], updates)

    def test_ble_link_sends_command_and_collects_prompt_terminated_response(self) -> None:
        async def run_link() -> str:
            client = FakeBleClient()
            link = BleElm327Link(client, "rx-uuid", "tx-uuid")
            await link.start()
            response = await link.send("010D")
            self.assertEqual([("tx-uuid", b"010D\r", False)], client.writes)
            return response

        self.assertEqual("41 0D 2A", asyncio.run(run_link()))


if __name__ == "__main__":
    unittest.main()
