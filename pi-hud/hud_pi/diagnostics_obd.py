from __future__ import annotations

import asyncio
import time
from typing import Any

from .diagnostics_common import DiagnosticResult, compact_response


def send_elm_command(link: Any, command: str, size: int = 1024) -> str:
    link.write((command + "\r").encode("ascii"))
    link.flush()
    raw = link.read_until(b">", size=size).decode("ascii", errors="ignore")
    return raw.replace("\r", "\n").replace(">", "").strip()


class _BleElmCommandLink:
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

    async def send(self, command: str, size: int = 1024) -> str:
        self.buffer.clear()
        self.response_event.clear()
        await self.client.write_gatt_char(self.tx_uuid, (command + "\r").encode("ascii"), response=False)
        try:
            await asyncio.wait_for(self.response_event.wait(), timeout=self.timeout)
        except asyncio.TimeoutError:
            pass
        raw = bytes(self.buffer[:size]).decode("ascii", errors="ignore")
        return raw.replace("\r", "\n").replace(">", "").strip()


async def _run_ble_elm_commands(mac: str, rx_uuid: str, tx_uuid: str, commands: list[str] | tuple[str, ...], timeout: float) -> list[str]:
    from bleak import BleakClient

    async with BleakClient(mac, timeout=timeout) as client:
        link = _BleElmCommandLink(client, rx_uuid, tx_uuid, timeout=timeout)
        await link.start()
        for command in ("ATZ", "ATE0", "ATL0"):
            await link.send(command)
            await asyncio.sleep(0.15)
        responses = []
        for command in commands:
            responses.append(await link.send(command))
        return responses


def run_ble_elm_commands(mac: str, rx_uuid: str, tx_uuid: str, commands: list[str] | tuple[str, ...], timeout: float = 2.0) -> list[str]:
    if not mac:
        raise ValueError("missing BLE MAC")
    if not rx_uuid or not tx_uuid:
        raise ValueError("missing RX/TX UUID")
    return asyncio.run(_run_ble_elm_commands(mac, rx_uuid, tx_uuid, commands, timeout))


def probe_obd(port: str, baudrate: int = 38400, timeout: float = 2.0) -> DiagnosticResult:
    try:
        import serial
    except ImportError:
        return DiagnosticResult("obd", False, "pyserial is not installed")

    try:
        with serial.Serial(port, baudrate, timeout=timeout, write_timeout=timeout) as link:
            send_elm_command(link, "ATZ")
            time.sleep(0.5)
            send_elm_command(link, "ATE0")
            send_elm_command(link, "ATL0")
            identity = compact_response(send_elm_command(link, "ATI"))
            supported = compact_response(send_elm_command(link, "0100"))
    except OSError as exc:
        return DiagnosticResult("obd", False, f"{port} open/read error: {exc.__class__.__name__}")

    if not identity and not supported:
        return DiagnosticResult("obd", False, f"{port} responded with empty data")
    if "NO DATA" in supported.upper() or "UNABLE" in supported.upper():
        return DiagnosticResult("obd", False, f"{port} command failed: ATI={identity!r}, 0100={supported!r}")
    return DiagnosticResult("obd", True, f"{port} {baudrate} baud, ATI={identity!r}, 0100={supported!r}")


def probe_obd_ble(mac: str, rx_uuid: str, tx_uuid: str, timeout: float = 2.0) -> DiagnosticResult:
    if not mac:
        return DiagnosticResult("obd-ble", False, "missing BLE MAC")
    if not rx_uuid or not tx_uuid:
        return DiagnosticResult("obd-ble", False, "missing RX/TX UUID")
    try:
        identity, supported = [compact_response(response) for response in run_ble_elm_commands(mac, rx_uuid, tx_uuid, ["ATI", "0100"], timeout=timeout)]
    except ImportError:
        return DiagnosticResult("obd-ble", False, "bleak is not installed")
    except ValueError as exc:
        return DiagnosticResult("obd-ble", False, str(exc))
    except Exception as exc:
        return DiagnosticResult("obd-ble", False, f"{mac} connect/read error: {exc.__class__.__name__}")

    if not identity and not supported:
        return DiagnosticResult("obd-ble", False, f"{mac} responded with empty data")
    if "NO DATA" in supported.upper() or "UNABLE" in supported.upper():
        return DiagnosticResult("obd-ble", False, f"{mac} command failed: ATI={identity!r}, 0100={supported!r}")
    return DiagnosticResult("obd-ble", True, f"{mac}, ATI={identity!r}, 0100={supported!r}")
