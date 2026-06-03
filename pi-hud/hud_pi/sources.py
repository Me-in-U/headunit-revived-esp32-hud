from __future__ import annotations

import asyncio
import json
import math
import re
import socket
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable

from .can_signals import decode_can_signals, merge_nested_update
from .discovery import build_discovery_hello, local_ip_for, parse_discovery_probe
from .obd import parse_dtc_response, payload_bytes_after
from .state import normalize_packet

StateCallback = Callable[[str, dict[str, Any]], None]


class SourceThread(threading.Thread):
    def __init__(self, callback: StateCallback, name: str) -> None:
        super().__init__(daemon=True, name=name)
        self.callback = callback
        self.stop_event = threading.Event()
        self.ready_event = threading.Event()

    def stop(self) -> None:
        self.stop_event.set()


class BridgeUdpReceiver(SourceThread):
    def __init__(self, callback: StateCallback, port: int, allow_diagnostic_packets: bool = False) -> None:
        super().__init__(callback, "bridge-udp")
        self.port = port
        self.allow_diagnostic_packets = allow_diagnostic_packets
        self.last_sequence: int | None = None

    def run(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("", self.port))
            sock.settimeout(0.5)
            self.ready_event.set()
            while not self.stop_event.is_set():
                try:
                    data, _addr = sock.recvfrom(8192)
                except socket.timeout:
                    continue
                try:
                    packet = json.loads(data.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
                if not self._accept_packet(packet):
                    continue
                source, update = normalize_packet(packet, allow_diagnostic_packets=self.allow_diagnostic_packets)
                self.callback(source, update)
        finally:
            sock.close()

    def _accept_packet(self, packet: Any) -> bool:
        if not isinstance(packet, dict):
            return False
        raw_sequence = packet.get("seq")
        if raw_sequence is None:
            return True
        try:
            sequence = int(raw_sequence)
        except (TypeError, ValueError):
            return True
        if self.last_sequence is not None and sequence <= self.last_sequence:
            return False
        self.last_sequence = sequence
        return True


class BridgeDiscoveryResponder(SourceThread):
    def __init__(self, callback: StateCallback, discovery_port: int, hud_port: int, name: str = "Headunit Pi HUD") -> None:
        super().__init__(callback, "bridge-discovery")
        self.discovery_port = discovery_port
        self.hud_port = hud_port
        self.name = name

    def run(self) -> None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(("", self.discovery_port))
            sock.settimeout(0.5)
        except OSError as exc:
            self.callback("bridge", {"nav": {"discovery_state": f"error:{exc.__class__.__name__}"}})
            self.ready_event.set()
            return

        last_hello_at = 0.0
        self.ready_event.set()
        self.callback("bridge", {"nav": {"discovery_state": "listening"}})
        while not self.stop_event.is_set():
            now = time.monotonic()
            if now - last_hello_at >= 5.0:
                last_hello_at = now
                self._send_hello(sock, ("255.255.255.255", self.discovery_port))
            try:
                data, addr = sock.recvfrom(2048)
            except socket.timeout:
                continue
            if not parse_discovery_probe(data):
                continue
            self._send_hello(sock, addr)
        sock.close()

    def _send_hello(self, sock: socket.socket, addr: tuple[str, int]) -> None:
        ip_address = local_ip_for(addr[0])
        payload = build_discovery_hello(self.name, ip_address, self.hud_port)
        try:
            sock.sendto(payload, addr)
        except OSError:
            return


class DummyVehicleSource(SourceThread):
    def __init__(self, callback: StateCallback) -> None:
        super().__init__(callback, "dummy-vehicle")
        self.start_time = time.monotonic()

    def run(self) -> None:
        while not self.stop_event.is_set():
            elapsed = time.monotonic() - self.start_time
            speed = max(0, int(42 + 12 * math.sin(elapsed / 4)))
            rpm = int(1200 + speed * 24 + 160 * math.sin(elapsed))
            self.callback(
                "dummy",
                {
                    "vehicle": {
                        "speed_kmh": speed,
                        "rpm": rpm,
                        "coolant_c": 88,
                        "voltage_v": 14.1,
                        "gear_range": "D",
                        "source": "dummy",
                        "obd_state": "dummy",
                        "can_state": "dummy",
                    },
                    "warnings": {
                        "door_open": False,
                        "battery": False,
                        "brake": False,
                        "abs": False,
                        "airbag": False,
                        "oil_pressure": False,
                        "check_engine": False,
                        "eps": False,
                        "coolant_temp": False,
                        "eco": True,
                    },
                },
            )
            time.sleep(0.25)


class Elm327PollingMixin:
    last_obd_request: str
    last_obd_response: str

    def _base_live_vehicle_update(self) -> dict[str, Any]:
        return {"vehicle": {"source": "pi-obd", "obd_state": "live"}}

    def _hex_bytes(self, response: str, service_pid: str) -> list[int]:
        return payload_bytes_after(response, service_pid)

    def _parse_byte_pid_response(self, response: str, service_pid: str, offset: int = 0) -> int | None:
        bytes_ = self._hex_bytes(response, service_pid)
        if not bytes_:
            return None
        return bytes_[0] + offset

    def _parse_rpm_response(self, response: str) -> int | None:
        bytes_ = self._hex_bytes(response, "410C")
        if len(bytes_) < 2:
            return None
        return int(((bytes_[0] * 256) + bytes_[1]) / 4)

    def _parse_voltage_response(self, response: str) -> float | None:
        bytes_ = self._hex_bytes(response, "4142")
        if len(bytes_) >= 2:
            return round(((bytes_[0] * 256) + bytes_[1]) / 1000, 1)
        return None

    def _parse_adapter_voltage(self, response: str) -> float | None:
        match = re.search(r"([-+]?\d+(?:\.\d+)?)\s*V\b", response.upper())
        if match is None:
            return None
        try:
            return round(float(match.group(1)), 1)
        except ValueError:
            return None

    def _parse_mil_response(self, response: str) -> tuple[bool | None, int | None]:
        bytes_ = self._hex_bytes(response, "4101")
        if not bytes_:
            return None, None
        return bool(bytes_[0] & 0x80), bytes_[0] & 0x7F


class Elm327ObdSource(SourceThread, Elm327PollingMixin):
    def __init__(self, callback: StateCallback, port: str, baudrate: int = 38400) -> None:
        super().__init__(callback, "elm327-obd")
        self.port = port
        self.baudrate = baudrate
        self.last_obd_request = ""
        self.last_obd_response = ""

    def run(self) -> None:
        try:
            import serial
        except ImportError:
            self.callback("obd", {"vehicle": {"obd_state": "pyserial-missing"}})
            return
        try:
            with serial.Serial(self.port, self.baudrate, timeout=1) as link:
                for command in ("ATZ", "ATE0", "ATL0", "ATS0", "ATH1", "ATSP0"):
                    self._send(link, command)
                    time.sleep(0.15)
                last_dtc_at = 0.0
                while not self.stop_event.is_set():
                    update = self._base_live_vehicle_update()
                    update["vehicle"]["rpm"] = self._read_rpm(link)
                    update["vehicle"]["speed_kmh"] = self._read_byte_pid(link, "010D")
                    update["vehicle"]["coolant_c"] = self._read_byte_pid(link, "0105", offset=-40)
                    voltage = self._read_voltage(link)
                    if voltage is not None:
                        update["vehicle"]["voltage_v"] = voltage
                    mil, count = self._read_mil(link)
                    update["dtc"] = {"mil": mil, "count": count}
                    if mil is not None:
                        update["warnings"] = {"check_engine": mil}
                    if time.monotonic() - last_dtc_at >= 5.0:
                        last_dtc_at = time.monotonic()
                        stored = self._read_dtcs(link, "03", "43")
                        pending = self._read_dtcs(link, "07", "47")
                        permanent = self._read_dtcs(link, "0A", "4A")
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
                    time.sleep(0.5)
        except OSError as exc:
            self.callback("obd", {"vehicle": {"obd_state": f"error:{exc.__class__.__name__}"}})

    def _send(self, link: Any, command: str) -> str:
        link.write((command + "\r").encode("ascii"))
        link.flush()
        raw = link.read_until(b">", size=512).decode("ascii", errors="ignore")
        response = raw.replace("\r", "\n").replace(">", "").strip()
        self.last_obd_request = command
        self.last_obd_response = response
        return response

    def _read_byte_pid(self, link: Any, request: str, offset: int = 0) -> int | None:
        response = self._send(link, request)
        return self._parse_byte_pid_response(response, "41" + request[2:], offset=offset)

    def _read_rpm(self, link: Any) -> int | None:
        return self._parse_rpm_response(self._send(link, "010C"))

    def _read_voltage(self, link: Any) -> float | None:
        voltage = self._parse_voltage_response(self._send(link, "0142"))
        if voltage is not None:
            return voltage
        return self._parse_adapter_voltage(self._send(link, "ATRV"))

    def _read_mil(self, link: Any) -> tuple[bool | None, int | None]:
        return self._parse_mil_response(self._send(link, "0101"))

    def _read_dtcs(self, link: Any, request: str, positive_service: str) -> list[str]:
        response = self._send(link, request)
        return parse_dtc_response(response, positive_service)


class _BleElm327Link:
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
            link = _BleElm327Link(client, self.rx_uuid, self.tx_uuid)
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

    async def _send(self, link: _BleElm327Link, command: str) -> str:
        response = await link.send(command)
        self.last_obd_request = command
        self.last_obd_response = response
        return response


@dataclass
class CanFrameSummary:
    frame_count: int = 0
    last_arbitration_id: int | None = None


class SocketCanSource(SourceThread):
    def __init__(self, callback: StateCallback, channel: str = "can0", signal_definitions: list[dict[str, Any]] | None = None) -> None:
        super().__init__(callback, "socketcan")
        self.channel = channel
        self.signal_definitions = signal_definitions or []

    def run(self) -> None:
        try:
            import can
        except ImportError:
            self.callback("can", {"vehicle": {"can_state": "python-can-missing"}})
            return
        summary = CanFrameSummary()
        try:
            try:
                bus = can.interface.Bus(channel=self.channel, interface="socketcan")
            except TypeError:
                bus = can.interface.Bus(channel=self.channel, bustype="socketcan")
            while not self.stop_event.is_set():
                message = bus.recv(timeout=0.5)
                if message is None:
                    continue
                summary.frame_count += 1
                summary.last_arbitration_id = int(message.arbitration_id)
                update = {
                    "vehicle": {
                        "can_state": "live",
                    },
                    "debug": {
                        "can_frame_count": summary.frame_count,
                        "last_can_id": hex(summary.last_arbitration_id),
                    },
                }
                decoded = decode_can_signals(summary.last_arbitration_id, bytes(message.data), self.signal_definitions)
                merge_nested_update(update, decoded)
                self.callback("can", update)
        except Exception as exc:
            self.callback("can", {"vehicle": {"can_state": f"error:{exc.__class__.__name__}"}})
