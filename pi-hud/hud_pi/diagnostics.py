from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, MutableMapping

from .layout import load_layout
from .layout_verifier import verify_layout_file


@dataclass(frozen=True)
class DiagnosticResult:
    name: str
    ok: bool
    detail: str


def format_result(result: DiagnosticResult) -> str:
    marker = "OK" if result.ok else "FAIL"
    return f"[{marker}] {result.name}: {result.detail}"


def load_env_file(path: str | Path, environ: MutableMapping[str, str], override: bool = False) -> list[str]:
    env_path = Path(path)
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []

    loaded: list[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        if key in environ and not override:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        environ[key] = value
        loaded.append(key)
    return loaded


def layout_summary(path: str | Path, width: int = 1920, height: int = 480, require_handoff: bool = False) -> DiagnosticResult:
    try:
        layout = load_layout(path)
    except OSError as exc:
        return DiagnosticResult("layout", False, f"cannot open: {exc}")
    except ValueError as exc:
        return DiagnosticResult("layout", False, f"invalid json: {exc}")

    canvas = layout.get("canvas", {})
    canvas_width = canvas.get("width", width)
    canvas_height = canvas.get("height", height)
    elements = layout.get("elements", [])
    vehicle = layout.get("selected_vehicle", "unknown")
    result = verify_layout_file(path, width=width, height=height, require_handoff=require_handoff)
    if not result.ok:
        return DiagnosticResult("layout", False, "; ".join(result.errors))
    return DiagnosticResult("layout", True, f"{canvas_width}x{canvas_height}, elements={len(elements)}, vehicle={vehicle}")


def probe_display(width: int = 1920, height: int = 480, framebuffer_virtual_size: str | Path = "/sys/class/graphics/fb0/virtual_size") -> DiagnosticResult:
    fb_path = Path(framebuffer_virtual_size)
    try:
        raw = fb_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        return DiagnosticResult("display", False, f"cannot read {fb_path}: {exc.__class__.__name__}")

    try:
        actual_width, actual_height = parse_framebuffer_virtual_size(raw)
    except ValueError as exc:
        return DiagnosticResult("display", False, f"invalid framebuffer size {raw!r}: {exc}")

    if actual_width != width or actual_height != height:
        return DiagnosticResult("display", False, f"framebuffer={actual_width}x{actual_height}, expected {width}x{height}")
    return DiagnosticResult("display", True, f"framebuffer={actual_width}x{actual_height}")


def parse_framebuffer_virtual_size(value: str) -> tuple[int, int]:
    normalized = value.strip().replace("x", ",").replace(" ", ",")
    parts = [part for part in normalized.split(",") if part]
    if len(parts) != 2:
        raise ValueError("expected WIDTH,HEIGHT")
    width, height = (int(part) for part in parts)
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    return width, height


def send_elm_command(link: Any, command: str, size: int = 1024) -> str:
    link.write((command + "\r").encode("ascii"))
    link.flush()
    raw = link.read_until(b">", size=size).decode("ascii", errors="ignore")
    return raw.replace("\r", "\n").replace(">", "").strip()


def compact_response(response: str) -> str:
    return " ".join(part.strip() for part in response.splitlines() if part.strip())


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


def open_socketcan_bus(can_module: Any, channel: str) -> Any:
    try:
        return can_module.interface.Bus(channel=channel, interface="socketcan")
    except TypeError:
        return can_module.interface.Bus(channel=channel, bustype="socketcan")


def probe_can(channel: str, timeout: float = 3.0) -> DiagnosticResult:
    try:
        import can
    except ImportError:
        return DiagnosticResult("can", False, "python-can is not installed")

    try:
        bus = open_socketcan_bus(can, channel)
    except Exception as exc:
        return DiagnosticResult("can", False, f"{channel} open error: {exc.__class__.__name__}")

    frame_count = 0
    last_id: int | None = None
    deadline = time.monotonic() + timeout
    try:
        while time.monotonic() < deadline:
            remaining = max(0.05, min(0.5, deadline - time.monotonic()))
            message = bus.recv(timeout=remaining)
            if message is None:
                continue
            frame_count += 1
            last_id = int(message.arbitration_id)
    except Exception as exc:
        return DiagnosticResult("can", False, f"{channel} receive error: {exc.__class__.__name__}")
    finally:
        shutdown = getattr(bus, "shutdown", None)
        if callable(shutdown):
            shutdown()

    if frame_count == 0:
        return DiagnosticResult("can", False, f"{channel} opened but no CAN frames within {timeout:.1f}s")
    return DiagnosticResult("can", True, f"{channel} frames={frame_count}, last_id=0x{last_id:X}")
