from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Callable, Mapping

from .diagnostics_common import DiagnosticResult


@dataclass(frozen=True)
class BluetoothDevice:
    mac: str
    name: str


@dataclass(frozen=True)
class BleObdPair:
    rx_uuid: str
    tx_uuid: str


@dataclass(frozen=True)
class AutoConfigResult:
    updates: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


RfcommBindFunc = Callable[[str, int, int], str]
ProbeSerialObdFunc = Callable[[str, int], DiagnosticResult]
DiscoverBleObdFunc = Callable[[str], list[BleObdPair]]
ProbeBleObdFunc = Callable[[str, str, str], DiagnosticResult]
SetupCanFunc = Callable[[str, int, str], None]
ProbeCanFunc = Callable[[str], DiagnosticResult]


OBD_NAME_KEYWORDS = (
    "icar",
    "obd",
    "obdii",
    "elm327",
    "v-link",
    "vlink",
    "vgate",
    "veepeak",
)


def parse_bluetoothctl_devices(output: str) -> list[BluetoothDevice]:
    devices: list[BluetoothDevice] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line.startswith("Device "):
            continue
        parts = line.split(maxsplit=2)
        if len(parts) < 3:
            continue
        devices.append(BluetoothDevice(parts[1], parts[2].strip()))
    return devices


def select_obd_candidate(devices: list[BluetoothDevice]) -> BluetoothDevice | None:
    candidates = [device for device in devices if _looks_like_obd_name(device.name)]
    if len(candidates) != 1:
        return None
    return candidates[0]


def _looks_like_obd_name(name: str) -> bool:
    normalized = name.strip().lower()
    compact = normalized.replace(" ", "").replace("_", "").replace("-", "")
    return any(keyword in normalized or keyword.replace("-", "") in compact for keyword in OBD_NAME_KEYWORDS)


def parse_can_channels(ip_link_output: str) -> list[str]:
    channels: set[str] = set()
    for raw_line in ip_link_output.splitlines():
        match = re.match(r"\d+:\s+([^:@]+)(?:@[^:]+)?:", raw_line.strip())
        if not match:
            continue
        name = match.group(1)
        if re.fullmatch(r"can\d+", name):
            channels.add(name)
    return sorted(channels, key=_can_channel_sort_key)


def _can_channel_sort_key(channel: str) -> tuple[int, int, str]:
    number_text = channel[3:]
    number = int(number_text) if number_text.isdigit() else 999
    return (0 if channel == "can0" else 1, number, channel)


def merge_env_updates(env_text: str, updates: Mapping[str, str]) -> str:
    if not updates:
        return env_text if env_text.endswith("\n") or not env_text else env_text + "\n"

    lines = env_text.splitlines()
    seen: set[str] = set()
    rendered: list[str] = []
    for line in lines:
        key = _env_line_key(line)
        if key in updates:
            rendered.append(f"{key}={updates[key]}")
            seen.add(key)
        else:
            rendered.append(line)

    if rendered and rendered[-1] != "":
        rendered.append("")
    for key, value in updates.items():
        if key not in seen:
            rendered.append(f"{key}={value}")
    return "\n".join(rendered).rstrip("\n") + "\n"


def _env_line_key(line: str) -> str | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return None
    if stripped.startswith("export "):
        stripped = stripped[len("export ") :].strip()
    key = stripped.split("=", 1)[0].strip()
    return key or None


def auto_configure_hardware(
    environ: Mapping[str, str],
    *,
    bluetooth_devices: list[BluetoothDevice],
    can_channels: list[str],
    rfcomm_bind: RfcommBindFunc,
    probe_serial_obd: ProbeSerialObdFunc,
    discover_ble_obd: DiscoverBleObdFunc,
    probe_ble_obd: ProbeBleObdFunc,
    setup_can: SetupCanFunc,
    probe_can_channel: ProbeCanFunc,
    force: bool = False,
) -> AutoConfigResult:
    updates: dict[str, str] = {}
    notes: list[str] = []
    issues: list[str] = []

    if force or not _obd_configured(environ):
        _configure_obd(environ, bluetooth_devices, rfcomm_bind, probe_serial_obd, discover_ble_obd, probe_ble_obd, updates, notes, issues)
    else:
        notes.append("OBD/iCar is already configured; leaving it unchanged")

    if force or not _can_configured(environ):
        _configure_can(environ, can_channels, setup_can, probe_can_channel, updates, notes, issues)
    else:
        notes.append("CANable is already configured; leaving it unchanged")

    return AutoConfigResult(updates=updates, notes=notes, issues=issues)


def _obd_configured(environ: Mapping[str, str]) -> bool:
    return bool(
        str(environ.get("HEADUNIT_HUD_OBD_PORT", "")).strip()
        or str(environ.get("HEADUNIT_HUD_OBD_BLE_MAC", "")).strip()
    )


def _can_configured(environ: Mapping[str, str]) -> bool:
    return bool(str(environ.get("HEADUNIT_HUD_CAN_CHANNEL", "")).strip())


def _configure_obd(
    environ: Mapping[str, str],
    bluetooth_devices: list[BluetoothDevice],
    rfcomm_bind: RfcommBindFunc,
    probe_serial_obd: ProbeSerialObdFunc,
    discover_ble_obd: DiscoverBleObdFunc,
    probe_ble_obd: ProbeBleObdFunc,
    updates: dict[str, str],
    notes: list[str],
    issues: list[str],
) -> None:
    candidate = select_obd_candidate(bluetooth_devices)
    if candidate is None:
        issues.append("iCar/ELM327 Bluetooth device was not found or was ambiguous")
        return

    baud = _env_int(environ, "HEADUNIT_HUD_OBD_BAUD", 38400)
    rfcomm_index = _env_int(environ, "HEADUNIT_HUD_RFCOMM_INDEX", 0)
    rfcomm_channel = _env_int(environ, "HEADUNIT_HUD_RFCOMM_CHANNEL", 1)
    try:
        port = rfcomm_bind(candidate.mac, rfcomm_index, rfcomm_channel).strip() or f"/dev/rfcomm{rfcomm_index}"
        serial_result = probe_serial_obd(port, baud)
    except Exception as exc:
        port = f"/dev/rfcomm{rfcomm_index}"
        serial_result = DiagnosticResult("obd", False, f"rfcomm setup failed: {exc.__class__.__name__}")

    if serial_result.ok:
        updates.update(
            {
                "HEADUNIT_HUD_OBD_PORT": port,
                "HEADUNIT_HUD_ICAR_MAC": candidate.mac,
                "HEADUNIT_HUD_RFCOMM_INDEX": str(rfcomm_index),
                "HEADUNIT_HUD_RFCOMM_CHANNEL": str(rfcomm_channel),
            }
        )
        notes.append(f"Configured iCar/ELM327 over rfcomm: {candidate.name} {candidate.mac}")
        return

    notes.append(f"rfcomm OBD probe failed: {serial_result.detail}")
    try:
        pairs = discover_ble_obd(candidate.mac)
    except Exception as exc:
        issues.append(f"BLE OBD discovery failed for {candidate.mac}: {exc.__class__.__name__}")
        return

    if not pairs:
        issues.append(f"BLE OBD discovery found no RX/TX pair for {candidate.mac}")
        return

    pair = pairs[0]
    ble_result = probe_ble_obd(candidate.mac, pair.rx_uuid, pair.tx_uuid)
    if not ble_result.ok:
        issues.append(f"BLE OBD probe failed: {ble_result.detail}")
        return

    updates.update(
        {
            "HEADUNIT_HUD_OBD_PORT": "",
            "HEADUNIT_HUD_OBD_BLE_MAC": candidate.mac,
            "HEADUNIT_HUD_OBD_BLE_RX_UUID": pair.rx_uuid,
            "HEADUNIT_HUD_OBD_BLE_TX_UUID": pair.tx_uuid,
        }
    )
    notes.append(f"Configured iCar/ELM327 over BLE: {candidate.name} {candidate.mac}")


def _configure_can(
    environ: Mapping[str, str],
    can_channels: list[str],
    setup_can: SetupCanFunc,
    probe_can_channel: ProbeCanFunc,
    updates: dict[str, str],
    notes: list[str],
    issues: list[str],
) -> None:
    if not can_channels:
        issues.append("CANable SocketCAN channel was not found")
        return

    channel = can_channels[0]
    bitrate = _env_int(environ, "HEADUNIT_HUD_CAN_BITRATE", 500000)
    listen_only = str(environ.get("HEADUNIT_HUD_CAN_LISTEN_ONLY", "on")).strip() or "on"
    try:
        setup_can(channel, bitrate, listen_only)
    except Exception as exc:
        issues.append(f"CANable setup failed for {channel}: {exc.__class__.__name__}")
        return

    updates.update(
        {
            "HEADUNIT_HUD_CAN_CHANNEL": channel,
            "HEADUNIT_HUD_CAN_BITRATE": str(bitrate),
            "HEADUNIT_HUD_CAN_LISTEN_ONLY": listen_only,
        }
    )
    can_result = probe_can_channel(channel)
    if can_result.ok:
        notes.append(f"Configured CANable SocketCAN: {can_result.detail}")
    else:
        issues.append(f"CANable probe warning: {can_result.detail}")


def _env_int(environ: Mapping[str, str], key: str, fallback: int) -> int:
    try:
        return int(str(environ.get(key, fallback)).strip())
    except (TypeError, ValueError):
        return fallback
