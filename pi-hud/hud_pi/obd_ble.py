from __future__ import annotations

import asyncio
import time
from typing import Any

from .obd import parse_dtc_response
from .obd_polling import Elm327PollingMixin
from .source_threads import SourceThread, StateCallback


class BleElm327Link:
    def __init__(self, client: Any, rx_uuid: str, tx_uuid: str, timeout: float = 2.0) -> None:
        self.client = client
        self.rx_uuid = rx_uuid
        self.tx_uuid = tx_uuid
        self.timeout = timeout
        self.buffer = bytearray()
        self.response_event = asyncio.Event()

    async def start(self) -> None:
        await self.client.start_notify(self.rx_uuid, self._on_notify)

    def _on_notify(self, _sender: Any, data: bytearray) -> None:
        self.buffer.extend(bytes(data))
        if b">" in self.buffer:
            self.response_event.set()

    async def send(self, command: str) -> str:
        self.buffer.clear()
        self.response_event.clear()
        await self.client.write_gatt_char(self.tx_uuid, (command + "\r").encode("ascii"), response=False)
        try:
            await asyncio.wait_for(self.response_event.wait(), timeout=self.timeout)
        except asyncio.TimeoutError:
            pass
        raw = bytes(self.buffer).decode("ascii", errors="ignore")
        return raw.replace("\r", "\n").replace(">", "").strip()


_BleElm327Link = BleElm327Link


class BleElm327ObdSource(SourceThread, Elm327PollingMixin):
    def __init__(self, callback: StateCallback, mac: str, rx_uuid: str, tx_uuid: str) -> None:
        super().__init__(callback, "ble-elm327-obd")
        self.mac = mac
        self.rx_uuid = rx_uuid
        self.tx_uuid = tx_uuid
        self.last_obd_request = ""
        self.last_obd_response = ""

    def run(self) -> None:
        if not self.mac or not self.rx_uuid or not self.tx_uuid:
            self.callback("obd", {"vehicle": {"obd_state": "ble-config-missing"}})
            return
        try:
            asyncio.run(self._run_ble())
        except ImportError:
            self.callback("obd", {"vehicle": {"obd_state": "bleak-missing"}})
        except Exception as exc:
            self.callback("obd", {"vehicle": {"obd_state": f"error:{exc.__class__.__name__}"}})

    async def _run_ble(self) -> None:
        from bleak import BleakClient

        async with BleakClient(self.mac) as client:
            link = BleElm327Link(client, self.rx_uuid, self.tx_uuid)
            await link.start()
            for command in ("ATZ", "ATE0", "ATL0", "ATS0", "ATH1", "ATSP0"):
                await self._send(link, command)
                await asyncio.sleep(0.15)
            last_dtc_at = 0.0
            while not self.stop_event.is_set():
                update = self._base_live_vehicle_update()
                update["vehicle"]["rpm"] = self._parse_rpm_response(await self._send(link, "010C"))
                update["vehicle"]["speed_kmh"] = self._parse_byte_pid_response(await self._send(link, "010D"), "410D")
                update["vehicle"]["coolant_c"] = self._parse_byte_pid_response(await self._send(link, "0105"), "4105", offset=-40)
                voltage = self._parse_voltage_response(await self._send(link, "0142"))
                if voltage is None:
                    voltage = self._parse_adapter_voltage(await self._send(link, "ATRV"))
                if voltage is not None:
                    update["vehicle"]["voltage_v"] = voltage
                mil, count = self._parse_mil_response(await self._send(link, "0101"))
                update["dtc"] = {"mil": mil, "count": count}
                if mil is not None:
                    update["warnings"] = {"check_engine": mil}
                if time.monotonic() - last_dtc_at >= 5.0:
                    last_dtc_at = time.monotonic()
                    stored = parse_dtc_response(await self._send(link, "03"), "43")
                    pending = parse_dtc_response(await self._send(link, "07"), "47")
                    permanent = parse_dtc_response(await self._send(link, "0A"), "4A")
                    update["dtc"].update(
                        {
                            "stored": stored,
                            "pending": pending,
                            "permanent": permanent,
                            "count": len(stored) + len(pending),
                        }
                    )
                update["debug"] = {
                    "obd_request": self.last_obd_request,
                    "obd_response": self.last_obd_response,
                }
                self.callback("obd", update)
                await asyncio.sleep(0.5)

    async def _send(self, link: BleElm327Link, command: str) -> str:
        response = await link.send(command)
        self.last_obd_request = command
        self.last_obd_response = response
        return response
