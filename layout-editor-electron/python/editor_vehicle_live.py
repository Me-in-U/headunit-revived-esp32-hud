from __future__ import annotations

import asyncio
import copy
import json
import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable

from editor_paths import ensure_pi_hud_path

ensure_pi_hud_path()

from hud_pi.ble_obd_discovery import (  # noqa: E402
    characteristic_infos_from_services,
    classify_ble_obd_characteristics,
)
from hud_pi.can_signals import merge_nested_update, selected_vehicle_can_signals  # noqa: E402
from hud_pi.obd import compact_hex, parse_dtc_response, payload_bytes_after  # noqa: E402
from hud_pi.obd_polling import Elm327PollingMixin  # noqa: E402
from hud_pi.diagnostics_common import compact_response  # noqa: E402
from hud_pi.diagnostics_obd import run_ble_elm_commands, send_elm_command  # noqa: E402
from editor_can_analysis import can_message_to_record, summarize_can_records  # noqa: E402


EventSink = Callable[[dict[str, Any]], None]

OBD_DISCOVERY_COMMANDS = ("ATI", "ATDP", "ATRV", "0100", "0120", "0140", "0160", "03", "07", "0A")
DEFAULT_OBD_POLL_COMMANDS = ("0101", "0104", "0105", "010B", "010C", "010D", "010E", "010F", "0110", "0111", "011C", "011F", "012F", "0133", "0142")
OBD_LIVE_COMMANDS = tuple(dict.fromkeys((*OBD_DISCOVERY_COMMANDS, *DEFAULT_OBD_POLL_COMMANDS)))
DEFAULT_SLCAN_TTY_BAUDRATE = 115200

FUEL_TYPES = {
    1: "Gasoline",
    2: "Methanol",
    3: "Ethanol",
    4: "Diesel",
    5: "LPG",
    6: "CNG",
    7: "Propane",
    8: "Electric",
    9: "Bifuel gasoline",
    10: "Bifuel methanol",
    11: "Bifuel ethanol",
    12: "Bifuel LPG",
    13: "Bifuel CNG",
    14: "Bifuel propane",
    15: "Bifuel electricity",
    16: "Bifuel electric/combustion",
    17: "Hybrid gasoline",
    18: "Hybrid ethanol",
    19: "Hybrid diesel",
    20: "Hybrid electric",
    21: "Hybrid mixed fuel",
    22: "Hybrid regenerative",
}

OBD_STANDARD_PID_DEFINITIONS = {
    "0101": {"label": "Monitor status since DTCs cleared", "decode": lambda b: f"MIL {'on' if b and b[0] & 0x80 else 'off'}, DTC {b[0] & 0x7F}" if b else None},
    "0103": {"label": "Fuel system status", "decode": lambda b: decode_hex_value(b[:2])},
    "0104": {"label": "Calculated engine load", "unit": "%", "path": "vehicle.engine_load_pct", "decode": lambda b: decode_pct(b)},
    "0105": {"label": "Engine coolant temperature", "unit": "C", "path": "vehicle.coolant_c", "decode": lambda b: decode_temp(b)},
    "0106": {"label": "Short term fuel trim bank 1", "unit": "%", "path": "vehicle.short_fuel_trim_b1_pct", "decode": lambda b: decode_trim(b)},
    "0107": {"label": "Long term fuel trim bank 1", "unit": "%", "path": "vehicle.long_fuel_trim_b1_pct", "decode": lambda b: decode_trim(b)},
    "0108": {"label": "Short term fuel trim bank 2", "unit": "%", "path": "vehicle.short_fuel_trim_b2_pct", "decode": lambda b: decode_trim(b)},
    "0109": {"label": "Long term fuel trim bank 2", "unit": "%", "path": "vehicle.long_fuel_trim_b2_pct", "decode": lambda b: decode_trim(b)},
    "010B": {"label": "Intake manifold absolute pressure", "unit": "kPa", "path": "vehicle.intake_manifold_kpa", "decode": lambda b: decode_u8(b)},
    "010C": {"label": "Engine RPM", "unit": "rpm", "path": "vehicle.rpm", "decode": lambda b: int(decode_u16(b) / 4) if len(b) >= 2 else None},
    "010D": {"label": "Vehicle speed", "unit": "km/h", "path": "vehicle.speed_kmh", "decode": lambda b: decode_u8(b)},
    "010E": {"label": "Timing advance", "unit": "deg", "path": "vehicle.timing_advance_deg", "decode": lambda b: round((b[0] / 2) - 64, 1) if b else None},
    "010F": {"label": "Intake air temperature", "unit": "C", "path": "vehicle.intake_air_c", "decode": lambda b: decode_temp(b)},
    "0110": {"label": "MAF air flow rate", "unit": "g/s", "path": "vehicle.maf_gps", "decode": lambda b: round(decode_u16(b) / 100, 2) if len(b) >= 2 else None},
    "0111": {"label": "Throttle position", "unit": "%", "path": "vehicle.throttle_pct", "decode": lambda b: decode_pct(b)},
    "011C": {"label": "OBD standards compliance", "path": "obd.standard_id", "decode": lambda b: decode_u8(b)},
    "011F": {"label": "Run time since engine start", "unit": "s", "path": "vehicle.engine_runtime_s", "decode": lambda b: decode_u16(b) if len(b) >= 2 else None},
    "0121": {"label": "Distance with MIL on", "unit": "km", "path": "vehicle.distance_with_mil_km", "decode": lambda b: decode_u16(b) if len(b) >= 2 else None},
    "0122": {"label": "Fuel rail pressure relative", "unit": "kPa", "path": "vehicle.fuel_rail_pressure_kpa", "decode": lambda b: round(decode_u16(b) * 0.079, 1) if len(b) >= 2 else None},
    "0123": {"label": "Fuel rail gauge pressure", "unit": "kPa", "path": "vehicle.fuel_rail_gauge_kpa", "decode": lambda b: decode_u16(b) * 10 if len(b) >= 2 else None},
    "012C": {"label": "Commanded EGR", "unit": "%", "path": "vehicle.commanded_egr_pct", "decode": lambda b: decode_pct(b)},
    "012D": {"label": "EGR error", "unit": "%", "path": "vehicle.egr_error_pct", "decode": lambda b: decode_trim(b)},
    "012E": {"label": "Commanded evaporative purge", "unit": "%", "path": "vehicle.evap_purge_pct", "decode": lambda b: decode_pct(b)},
    "012F": {"label": "Fuel tank level", "unit": "%", "path": "vehicle.fuel_level_pct", "decode": lambda b: decode_pct(b)},
    "0130": {"label": "Warm-ups since codes cleared", "path": "vehicle.warmups_since_clear", "decode": lambda b: decode_u8(b)},
    "0131": {"label": "Distance since codes cleared", "unit": "km", "path": "vehicle.distance_since_clear_km", "decode": lambda b: decode_u16(b) if len(b) >= 2 else None},
    "0132": {"label": "Evap vapor pressure", "unit": "Pa", "path": "vehicle.evap_vapor_pressure_pa", "decode": lambda b: round(decode_i16(b) / 4, 1) if len(b) >= 2 else None},
    "0133": {"label": "Barometric pressure", "unit": "kPa", "path": "vehicle.barometric_kpa", "decode": lambda b: decode_u8(b)},
    "013C": {"label": "Catalyst temperature B1S1", "unit": "C", "path": "vehicle.catalyst_b1s1_c", "decode": lambda b: round(decode_u16(b) / 10 - 40, 1) if len(b) >= 2 else None},
    "013D": {"label": "Catalyst temperature B2S1", "unit": "C", "path": "vehicle.catalyst_b2s1_c", "decode": lambda b: round(decode_u16(b) / 10 - 40, 1) if len(b) >= 2 else None},
    "013E": {"label": "Catalyst temperature B1S2", "unit": "C", "path": "vehicle.catalyst_b1s2_c", "decode": lambda b: round(decode_u16(b) / 10 - 40, 1) if len(b) >= 2 else None},
    "013F": {"label": "Catalyst temperature B2S2", "unit": "C", "path": "vehicle.catalyst_b2s2_c", "decode": lambda b: round(decode_u16(b) / 10 - 40, 1) if len(b) >= 2 else None},
    "0142": {"label": "Control module voltage", "unit": "V", "path": "vehicle.voltage_v", "decode": lambda b: round(decode_u16(b) / 1000, 2) if len(b) >= 2 else None},
    "0143": {"label": "Absolute load value", "unit": "%", "path": "vehicle.absolute_load_pct", "decode": lambda b: round(decode_u16(b) * 100 / 255, 1) if len(b) >= 2 else None},
    "0144": {"label": "Commanded equivalence ratio", "path": "vehicle.commanded_equivalence_ratio", "decode": lambda b: round(decode_u16(b) / 32768, 3) if len(b) >= 2 else None},
    "0145": {"label": "Relative throttle position", "unit": "%", "path": "vehicle.relative_throttle_pct", "decode": lambda b: decode_pct(b)},
    "0146": {"label": "Ambient air temperature", "unit": "C", "path": "vehicle.ambient_air_c", "decode": lambda b: decode_temp(b)},
    "0147": {"label": "Absolute throttle position B", "unit": "%", "path": "vehicle.throttle_b_pct", "decode": lambda b: decode_pct(b)},
    "0148": {"label": "Absolute throttle position C", "unit": "%", "path": "vehicle.throttle_c_pct", "decode": lambda b: decode_pct(b)},
    "0149": {"label": "Accelerator pedal position D", "unit": "%", "path": "vehicle.accelerator_pedal_d_pct", "decode": lambda b: decode_pct(b)},
    "014A": {"label": "Accelerator pedal position E", "unit": "%", "path": "vehicle.accelerator_pedal_e_pct", "decode": lambda b: decode_pct(b)},
    "014B": {"label": "Accelerator pedal position F", "unit": "%", "path": "vehicle.accelerator_pedal_f_pct", "decode": lambda b: decode_pct(b)},
    "014C": {"label": "Commanded throttle actuator", "unit": "%", "path": "vehicle.commanded_throttle_pct", "decode": lambda b: decode_pct(b)},
    "014D": {"label": "Time run with MIL on", "unit": "min", "path": "vehicle.time_with_mil_min", "decode": lambda b: decode_u16(b) if len(b) >= 2 else None},
    "014E": {"label": "Time since codes cleared", "unit": "min", "path": "vehicle.time_since_clear_min", "decode": lambda b: decode_u16(b) if len(b) >= 2 else None},
    "0151": {"label": "Fuel type", "path": "vehicle.fuel_type", "decode": lambda b: FUEL_TYPES.get(b[0], f"code {b[0]}") if b else None},
    "0152": {"label": "Ethanol fuel percentage", "unit": "%", "path": "vehicle.ethanol_pct", "decode": lambda b: decode_pct(b)},
    "015C": {"label": "Engine oil temperature", "unit": "C", "path": "vehicle.engine_oil_c", "decode": lambda b: decode_temp(b)},
    "015E": {"label": "Engine fuel rate", "unit": "L/h", "path": "vehicle.fuel_rate_lph", "decode": lambda b: round(decode_u16(b) * 0.05, 2) if len(b) >= 2 else None},
    "0161": {"label": "Driver demand engine torque", "unit": "%", "path": "vehicle.driver_demand_torque_pct", "decode": lambda b: b[0] - 125 if b else None},
    "0162": {"label": "Actual engine torque", "unit": "%", "path": "vehicle.actual_engine_torque_pct", "decode": lambda b: b[0] - 125 if b else None},
    "0163": {"label": "Engine reference torque", "unit": "Nm", "path": "vehicle.engine_reference_torque_nm", "decode": lambda b: decode_u16(b) if len(b) >= 2 else None},
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def status_event(source: str, state: str, detail: str = "") -> dict[str, Any]:
    return {
        "type": "status",
        "source": source,
        "state": state,
        "detail": detail,
        "updatedAt": utc_now(),
    }


def build_can_bus_kwargs(config: dict[str, Any]) -> dict[str, Any]:
    channel = str(config.get("channel", "")).strip()
    if not channel:
        raise ValueError("CAN channel is required")
    channel, channel_tty_baudrate = normalize_slcan_channel(channel)
    kwargs: dict[str, Any] = {
        "channel": channel,
        "interface": str(config.get("interface") or "slcan"),
    }
    bitrate = config.get("bitrate")
    if bitrate not in (None, ""):
        kwargs["bitrate"] = int(bitrate)
    tty_baudrate = config.get("ttyBaudrate", config.get("tty_baudrate"))
    if tty_baudrate in (None, ""):
        tty_baudrate = channel_tty_baudrate
    if tty_baudrate in (None, "") and kwargs["interface"] == "slcan" and is_windows_com_port(channel):
        tty_baudrate = DEFAULT_SLCAN_TTY_BAUDRATE
    if tty_baudrate not in (None, ""):
        kwargs["tty_baudrate"] = int(tty_baudrate)
    if "listenOnly" in config or "listen_only" in config:
        kwargs["listen_only"] = bool(config.get("listenOnly", config.get("listen_only")))
    return kwargs


def normalize_slcan_channel(channel: str) -> tuple[str, int | None]:
    if "@" not in channel:
        return channel, None
    device, raw_baudrate = channel.rsplit("@", 1)
    device = device.strip()
    raw_baudrate = raw_baudrate.strip()
    if not device or not raw_baudrate:
        return channel, None
    try:
        return device, int(raw_baudrate)
    except ValueError:
        return channel, None


def is_windows_com_port(channel: str) -> bool:
    text = channel.strip().upper()
    return text.startswith("COM") and text[3:].isdigit()


def open_can_bus(can_module: Any, config: dict[str, Any]) -> Any:
    kwargs = build_can_bus_kwargs(config)
    try:
        return can_module.interface.Bus(**kwargs)
    except TypeError:
        legacy_kwargs = dict(kwargs)
        legacy_kwargs["bustype"] = legacy_kwargs.pop("interface")
        return can_module.interface.Bus(**legacy_kwargs)


def exception_detail(prefix: str, exc: Exception) -> str:
    detail = str(exc).strip()
    suffix = f"{exc.__class__.__name__}: {detail}" if detail else exc.__class__.__name__
    return f"{prefix}: {suffix}"


def decode_u8(bytes_: list[int]) -> int | None:
    return bytes_[0] if bytes_ else None


def decode_u16(bytes_: list[int]) -> int:
    return (bytes_[0] * 256) + bytes_[1]


def decode_i16(bytes_: list[int]) -> int:
    value = decode_u16(bytes_)
    return value - 0x10000 if value & 0x8000 else value


def decode_pct(bytes_: list[int]) -> float | None:
    return round(bytes_[0] * 100 / 255, 1) if bytes_ else None


def decode_trim(bytes_: list[int]) -> float | None:
    return round((bytes_[0] - 128) * 100 / 128, 1) if bytes_ else None


def decode_temp(bytes_: list[int]) -> int | None:
    return bytes_[0] - 40 if bytes_ else None


def decode_hex_value(bytes_: list[int]) -> str | None:
    return " ".join(f"{byte:02X}" for byte in bytes_) if bytes_ else None


def obd_exception_detail(exc: Exception, config: dict[str, Any] | None = None) -> str:
    config = config or {}
    port = str(config.get("port", "")).strip()
    base = exception_detail("OBD serial read failed" if port else "OBD BLE read failed", exc)
    if port:
        return (
            f"{base}. Pair Android-vlink in Windows Bluetooth settings using PIN 1234, then enter its "
            "Classic Bluetooth COM port in the editor."
        )
    if exc.__class__.__name__ in {"TimeoutError", "BleakDeviceNotFoundError"}:
        return (
            f"{base}. If the adapter asks for a PIN, pair IOS-Vlink in Windows Bluetooth settings first "
            "using 1234, then reconnect in the editor."
        )
    return base


async def _scan_obd_ble_devices(timeout: float = 5.0) -> dict[str, Any]:
    from bleak import BleakScanner

    devices = await BleakScanner.discover(timeout=timeout)
    return {
        "ok": True,
        "devices": [
            {
                "address": str(getattr(device, "address", "")),
                "name": str(getattr(device, "name", "") or ""),
                "rssi": getattr(device, "rssi", None),
            }
            for device in devices
        ],
    }


def scan_obd_ble_devices(timeout: float = 5.0) -> dict[str, Any]:
    try:
        return asyncio.run(_scan_obd_ble_devices(timeout=timeout))
    except ImportError:
        return {"ok": False, "errors": ["bleak is not installed"], "devices": []}
    except Exception as exc:
        return {"ok": False, "errors": [exception_detail("BLE scan failed", exc)], "devices": []}


async def _inspect_obd_ble_device(mac: str, timeout: float = 5.0) -> dict[str, Any]:
    from bleak import BleakClient

    target = await resolve_ble_device(mac, timeout)
    async with BleakClient(target, timeout=timeout) as client:
        services = getattr(client, "services", None)
        if services is None:
            services = await client.get_services()
        characteristics = characteristic_infos_from_services(services)
    result = classify_ble_obd_characteristics(characteristics)
    errors = []
    if not result.pairs:
        errors.append(
            "No notify/write BLE ELM327 characteristic pair found. "
            "If this is IOS-Vlink on Windows, use Android-vlink Classic Bluetooth COM instead, or disconnect the phone and inspect again."
        )
    return {
        "ok": bool(result.pairs),
        "mac": mac,
        "rxCandidates": [item.__dict__ for item in result.rx_candidates],
        "txCandidates": [item.__dict__ for item in result.tx_candidates],
        "pairs": [item.__dict__ for item in result.pairs],
        "errors": errors,
    }


def inspect_obd_ble_device(mac: str, timeout: float = 5.0) -> dict[str, Any]:
    if not mac:
        return {"ok": False, "mac": "", "rxCandidates": [], "txCandidates": [], "pairs": [], "errors": ["BLE MAC is required"]}
    try:
        return asyncio.run(_inspect_obd_ble_device(mac, timeout=timeout))
    except ImportError:
        return {"ok": False, "mac": mac, "rxCandidates": [], "txCandidates": [], "pairs": [], "errors": ["bleak is not installed"]}
    except Exception as exc:
        return {
            "ok": False,
            "mac": mac,
            "rxCandidates": [],
            "txCandidates": [],
            "pairs": [],
            "errors": [exception_detail(f"{mac} inspect failed", exc)],
        }


async def resolve_ble_device(identifier: str, timeout: float = 5.0) -> Any:
    from bleak import BleakScanner

    wanted = str(identifier or "").strip()
    if not wanted:
        raise ValueError("missing BLE MAC")
    devices = await BleakScanner.discover(timeout=timeout)
    wanted_upper = wanted.upper()
    for device in devices:
        address = str(getattr(device, "address", "") or "")
        name = str(getattr(device, "name", "") or "")
        if address.upper() == wanted_upper or name.upper() == wanted_upper:
            return device
    return wanted


class _ObdParser(Elm327PollingMixin):
    last_obd_request = ""
    last_obd_response = ""


def build_obd_live_commands(supported_pids: set[int] | None = None) -> tuple[str, ...]:
    if not supported_pids:
        return OBD_LIVE_COMMANDS
    supported_commands = [
        f"01{pid:02X}"
        for pid in sorted(supported_pids)
        if pid not in {0x00, 0x20, 0x40, 0x60} and 0x01 <= pid <= 0x7F
    ]
    return tuple(dict.fromkeys((*OBD_DISCOVERY_COMMANDS, *supported_commands)))


def payload_byte_segments_after(response: str, positive_service: str, payload_length: int | None = None) -> list[list[int]]:
    compact = compact_hex(response)
    marker = positive_service.upper()
    segments: list[list[int]] = []
    start = 0
    while marker:
        index = compact.find(marker, start)
        if index < 0:
            break
        payload_start = index + len(marker)
        if payload_length is None:
            next_index = compact.find(marker, payload_start)
            payload = compact[payload_start : next_index if next_index >= 0 else len(compact)]
        else:
            payload = compact[payload_start : payload_start + payload_length * 2]
        if len(payload) >= 2:
            try:
                segments.append([int(payload[i : i + 2], 16) for i in range(0, len(payload) - 1, 2)])
            except ValueError:
                pass
        start = payload_start + max(2, len(payload))
    return segments


def supported_pids_from_records(records: list[dict[str, Any]]) -> set[int]:
    by_command = {str(record.get("command", "")).upper(): str(record.get("response", "")) for record in records}
    supported: set[int] = set()
    for command in ("0100", "0120", "0140", "0160"):
        response_prefix = f"41{command[2:]}"
        base = int(command[2:], 16)
        for bytes_ in payload_byte_segments_after(by_command.get(command, ""), response_prefix, payload_length=4):
            if len(bytes_) < 4:
                continue
            for byte_index, byte in enumerate(bytes_[:4]):
                for bit_index in range(8):
                    if byte & (1 << (7 - bit_index)):
                        supported.add(base + byte_index * 8 + bit_index + 1)
    return supported


def selected_vehicle_obd_pid_definitions(layout: dict[str, Any]) -> list[dict[str, Any]]:
    for vehicle in layout.get("vehicles", []):
        if vehicle.get("id") == layout.get("selected_vehicle"):
            definitions = vehicle.get("obd_pid_definitions", [])
            return [copy.deepcopy(item) for item in definitions if isinstance(item, dict)]
    return []


def normalize_obd_mode01_command(value: Any) -> str:
    text = compact_hex(str(value or "")).upper()
    if len(text) == 2:
        return f"01{text}"
    if len(text) == 4 and text.startswith("01"):
        return text
    return ""


def obd_pid_definition_map(definitions: list[dict[str, Any]] | None) -> dict[str, dict[str, Any]]:
    mapped: dict[str, dict[str, Any]] = {}
    for definition in definitions or []:
        command = normalize_obd_mode01_command(definition.get("command", definition.get("pid", "")))
        if command:
            mapped[command] = definition
    return mapped


def optional_int(value: Any, default: int | None = None) -> int | None:
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def optional_float(value: Any, default: float) -> float:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def custom_obd_value(command: str, definition: dict[str, Any], bytes_: list[int]) -> dict[str, Any] | None:
    label = str(definition.get("label") or definition.get("name") or command).strip() or command
    unit = str(definition.get("unit", "")).strip()
    path = str(definition.get("path") or definition.get("statePath") or "").strip()
    byte_index = max(0, optional_int(definition.get("byte_index", definition.get("byteIndex")), 0) or 0)
    byte_length = optional_int(definition.get("byte_length", definition.get("length", definition.get("byteLength"))))
    raw_text = decode_hex_value(bytes_) or ""
    value: Any = raw_text
    if byte_length:
        byte_length = max(1, min(4, byte_length))
        payload = bytes_[byte_index : byte_index + byte_length]
        if len(payload) < byte_length:
            return None
        endian = str(definition.get("endian") or "big").lower()
        byteorder = "little" if endian == "little" else "big"
        raw_number = int.from_bytes(bytes(payload), byteorder=byteorder, signed=bool(definition.get("signed")))
        decoded = raw_number * optional_float(definition.get("scale"), 1.0) + optional_float(definition.get("offset"), 0.0)
        value = int(decoded) if float(decoded).is_integer() else round(decoded, 4)
    return {
        "command": command,
        "label": label,
        "value": value,
        "unit": unit,
        "statePath": path,
        "rawBytes": raw_text,
        "custom": True,
    }


def decode_obd_value(command: str, response: str, custom_definitions: dict[str, dict[str, Any]] | None = None) -> dict[str, Any] | None:
    command = command.upper()
    if not command.startswith("01") or len(command) != 4:
        return None
    pid = command[2:]
    segments = payload_byte_segments_after(response, f"41{pid}")
    bytes_ = segments[0] if segments else []
    if not bytes_:
        return None
    raw_text = decode_hex_value(bytes_) or ""
    custom_definition = (custom_definitions or {}).get(command)
    if custom_definition is not None:
        return custom_obd_value(command, custom_definition, bytes_)
    definition = OBD_STANDARD_PID_DEFINITIONS.get(command)
    if definition is None:
        return {
            "command": command,
            "label": f"Mode 01 PID {pid}",
            "value": raw_text,
            "unit": "raw",
            "statePath": "",
            "rawBytes": raw_text,
        }
    try:
        value = definition["decode"](bytes_)
    except (IndexError, TypeError, ValueError, ZeroDivisionError):
        value = None
    if value is None:
        return None
    return {
        "command": command,
        "label": str(definition.get("label", command)),
        "value": value,
        "unit": str(definition.get("unit", "")),
        "statePath": str(definition.get("path", "")),
        "rawBytes": raw_text,
    }


def decoded_obd_values(records: list[dict[str, Any]], custom_definitions: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    values = []
    seen: set[str] = set()
    custom_definition_map = obd_pid_definition_map(custom_definitions)
    for record in records:
        command = str(record.get("command", "")).upper()
        if command in seen:
            continue
        seen.add(command)
        value = decode_obd_value(command, str(record.get("response", "")), custom_definition_map)
        if value is not None:
            values.append(value)
    return values


def apply_obd_values_to_update(update: dict[str, Any], values: list[dict[str, Any]]) -> None:
    for item in values:
        path = str(item.get("statePath", ""))
        if not path:
            continue
        set_nested_value(update, path, item.get("value"))


def set_nested_value(update: dict[str, Any], path: str, value: Any) -> None:
    parts = [part for part in path.split(".") if part]
    if not parts:
        return
    cursor = update
    for part in parts[:-1]:
        next_value = cursor.get(part)
        if not isinstance(next_value, dict):
            next_value = {}
            cursor[part] = next_value
        cursor = next_value
    cursor[parts[-1]] = value


def supported_pid_text(supported_pids: set[int]) -> str:
    if not supported_pids:
        return "--"
    return ", ".join(f"01{pid:02X}" for pid in sorted(supported_pids))


def supported_pid_bitmap_text(by_command: dict[str, str]) -> str:
    rows = []
    for command in ("0100", "0120", "0140", "0160"):
        response = compact_response(by_command.get(command, ""))
        if response:
            rows.append(f"{command}: {response}")
    return " | ".join(rows)


def build_obd_live_update(records: list[dict[str, Any]], custom_definitions: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    parser = _ObdParser()
    by_command = {str(record.get("command", "")): str(record.get("response", "")) for record in records}
    supported_pids = supported_pids_from_records(records)
    values = decoded_obd_values(records, custom_definitions)
    update: dict[str, Any] = {
        "vehicle": {
            "source": "windows-obd",
            "obd_state": "live",
        },
        "obd": {
            "adapter_identity": compact_response(by_command.get("ATI", "")),
            "protocol": compact_response(by_command.get("ATDP", "")),
            "supported_pid_bitmap": compact_response(by_command.get("0100", "")),
            "supported_pid_ranges": supported_pid_bitmap_text(by_command),
            "supported_pids": sorted(f"01{pid:02X}" for pid in supported_pids),
            "supported_pid_count": len(supported_pids),
            "value_count": len(values),
            "values": values,
        },
        "debug": {},
    }
    if records:
        update["debug"]["obd_request"] = records[-1].get("command", "")
        update["debug"]["obd_response"] = records[-1].get("response", "")
    rpm = parser._parse_rpm_response(by_command.get("010C", ""))
    speed = parser._parse_byte_pid_response(by_command.get("010D", ""), "410D")
    coolant = parser._parse_byte_pid_response(by_command.get("0105", ""), "4105", offset=-40)
    voltage = parser._parse_voltage_response(by_command.get("0142", ""))
    mil, count = parser._parse_mil_response(by_command.get("0101", ""))
    if voltage is None:
        voltage = parser._parse_adapter_voltage(by_command.get("ATRV", ""))
    for key, value in (("rpm", rpm), ("speed_kmh", speed), ("coolant_c", coolant), ("voltage_v", voltage)):
        if value is not None:
            update["vehicle"][key] = value
    apply_obd_values_to_update(update, values)
    update["dtc"] = {
        "mil": mil,
        "count": count,
        "stored": parse_dtc_response(by_command.get("03", ""), "43"),
        "pending": parse_dtc_response(by_command.get("07", ""), "47"),
        "permanent": parse_dtc_response(by_command.get("0A", ""), "4A"),
    }
    update["dtc"]["count"] = len(update["dtc"]["stored"]) + len(update["dtc"]["pending"]) if update["dtc"]["stored"] or update["dtc"]["pending"] else count
    return update


class VehicleLiveSession:
    def __init__(
        self,
        config: dict[str, Any],
        *,
        emit: EventSink,
        can_bus_factory: Callable[[dict[str, Any]], Any] | None = None,
        obd_command_runner: Callable[[dict[str, Any], tuple[str, ...]], list[str]] | None = None,
    ) -> None:
        self.config = copy.deepcopy(config)
        self.emit = emit
        self.can_bus_factory = can_bus_factory or self._default_can_bus_factory
        self.obd_command_runner = obd_command_runner or self._default_obd_command_runner
        self.stop_event = threading.Event()
        self.merged_state: dict[str, Any] = {}
        self.can_records: list[dict[str, Any]] = []
        self.obd_supported_pids: set[int] = set()
        self.obd_pid_definitions = selected_vehicle_obd_pid_definitions(self.config.get("layout", {}))
        self.signal_definitions = selected_vehicle_can_signals(self.config.get("layout", {}))

    def stop(self) -> None:
        self.stop_event.set()

    def run_forever(self) -> None:
        threads: list[threading.Thread] = []
        if self.config.get("can", {}).get("enabled"):
            threads.append(threading.Thread(target=self.run_can_loop, daemon=True))
        if self.config.get("obd", {}).get("enabled"):
            threads.append(threading.Thread(target=self.run_obd_loop, daemon=True))
        if not threads:
            self.emit(status_event("can", "idle", "CAN disabled"))
            self.emit(status_event("obd", "idle", "OBD disabled"))
            return
        for thread in threads:
            thread.start()
        try:
            while any(thread.is_alive() for thread in threads) and not self.stop_event.is_set():
                time.sleep(0.1)
        finally:
            self.stop_event.set()
            for thread in threads:
                thread.join(timeout=1.0)

    def run_can_once(self) -> None:
        config = self.config.get("can", {})
        if not config.get("enabled"):
            self.emit(status_event("can", "idle", "CAN disabled"))
            return
        self.emit(status_event("can", "connecting", can_open_detail(config)))
        bus = self.can_bus_factory(config)
        try:
            message = bus.recv(timeout=float(config.get("timeoutSeconds", 0.5)))
            if message is None:
                self.emit(status_event("can", "stale", no_can_frames_detail(config)))
                return
            self._process_can_message(message)
        finally:
            shutdown = getattr(bus, "shutdown", None)
            if callable(shutdown):
                shutdown()

    def run_can_loop(self) -> None:
        config = self.config.get("can", {})
        stale_seconds = max(1.0, float(config.get("staleSeconds", 3.0)))
        try:
            self.emit(status_event("can", "connecting", can_open_detail(config)))
            bus = self.can_bus_factory(config)
            self.emit(status_event("can", "live", f"CANable connected; waiting for frames on {can_channel_label(config)}"))
            last_frame_at = time.monotonic()
            stale_reported = False
            try:
                while not self.stop_event.is_set():
                    message = bus.recv(timeout=0.5)
                    if message is not None:
                        last_frame_at = time.monotonic()
                        stale_reported = False
                        self._process_can_message(message)
                    elif not stale_reported and time.monotonic() - last_frame_at >= stale_seconds:
                        self.emit(status_event("can", "stale", no_can_frames_detail(config)))
                        stale_reported = True
            finally:
                shutdown = getattr(bus, "shutdown", None)
                if callable(shutdown):
                    shutdown()
        except Exception as exc:
            self.emit(status_event("can", "error", f"{exc.__class__.__name__}: {exc}"))

    def run_obd_once(self, *, emit_connecting: bool = True) -> None:
        config = self.config.get("obd", {})
        if not config.get("enabled"):
            self.emit(status_event("obd", "idle", "OBD disabled"))
            return
        if emit_connecting:
            self.emit(status_event("obd", "connecting", obd_open_detail(config)))
        commands = build_obd_live_commands(self.obd_supported_pids)
        responses = self.obd_command_runner(config, commands)
        records = []
        for command, response in zip(commands, responses):
            record = {"command": command, "response": compact_response(response), "ok": bool(compact_response(response))}
            records.append(record)
            self.emit({"type": "obd_record", "source": "obd", "record": record, "updatedAt": utc_now()})
        detected_pids = supported_pids_from_records(records)
        if detected_pids:
            self.obd_supported_pids = detected_pids
        update = build_obd_live_update(records, self.obd_pid_definitions)
        self._emit_state("obd", update)
        value_count = update.get("obd", {}).get("value_count", 0)
        supported_count = update.get("obd", {}).get("supported_pid_count", 0)
        self.emit(status_event("obd", "live", f"{obd_live_detail(config)}; {value_count} decoded values, {supported_count} supported PIDs"))

    def run_obd_loop(self) -> None:
        interval = max(0.5, float(self.config.get("obd", {}).get("pollSeconds", 1.5)))
        emit_connecting = True
        while not self.stop_event.is_set():
            try:
                self.run_obd_once(emit_connecting=emit_connecting)
                emit_connecting = False
            except Exception as exc:
                self.emit(status_event("obd", "error", obd_exception_detail(exc, self.config.get("obd", {}))))
                emit_connecting = True
                if str(self.config.get("obd", {}).get("port", "")).strip():
                    break
            self.stop_event.wait(interval)

    def _process_can_message(self, message: Any) -> None:
        record = can_message_to_record(message)
        self.can_records.append(record)
        self.can_records = self.can_records[-500:]
        self.emit({"type": "can_frame", "source": "can", "record": record, "updatedAt": utc_now()})
        summary = summarize_can_records(self.can_records)
        self.emit({"type": "can_summary", "source": "can", "summary": summary, "updatedAt": utc_now()})
        update = {
            "vehicle": {"can_state": "live"},
            "debug": {"can_frame_count": len(self.can_records), "last_can_id": record["id"]},
        }
        decoded = self._decode_record(record)
        merge_nested_update(update, decoded)
        self._emit_state("can", update)
        self.emit(status_event("can", "live", f"{summary['frame_count']} frames"))

    def _decode_record(self, record: dict[str, Any]) -> dict[str, Any]:
        from hud_pi.can_signals import decode_can_signals

        try:
            frame_id = int(record["arbitration_id"])
            data = bytes(int(part, 16) for part in str(record["data"]).split())
        except (KeyError, TypeError, ValueError):
            return {}
        return decode_can_signals(frame_id, data, self.signal_definitions)

    def _emit_state(self, source: str, update: dict[str, Any]) -> None:
        merge_nested_update(self.merged_state, copy.deepcopy(update))
        self.emit(
            {
                "type": "state",
                "source": source,
                "update": update,
                "mergedState": copy.deepcopy(self.merged_state),
                "updatedAt": utc_now(),
            }
        )

    def _default_can_bus_factory(self, config: dict[str, Any]) -> Any:
        import can

        return open_can_bus(can, config)

    def _default_obd_command_runner(self, config: dict[str, Any], commands: tuple[str, ...]) -> list[str]:
        port = str(config.get("port", "")).strip()
        if port:
            return run_serial_elm_commands(
                port,
                int(config.get("baud") or config.get("baudrate") or 38400),
                commands,
                timeout=float(config.get("timeoutSeconds", 2.0)),
            )
        return run_ble_elm_commands(
            str(config.get("mac", "")),
            str(config.get("rxUuid") or config.get("rx_uuid") or ""),
            str(config.get("txUuid") or config.get("tx_uuid") or ""),
            list(commands),
            timeout=float(config.get("timeoutSeconds", 2.0)),
        )


def run_worker(config: dict[str, Any], emit: EventSink | None = None) -> None:
    sink = emit or (lambda event: print(json.dumps(event, ensure_ascii=False), flush=True))
    VehicleLiveSession(config, emit=sink).run_forever()


def run_serial_elm_commands(port: str, baudrate: int, commands: tuple[str, ...], timeout: float = 2.0) -> list[str]:
    import serial

    with serial.Serial(port, baudrate, timeout=timeout, write_timeout=timeout) as link:
        for command in ("ATZ", "ATE0", "ATL0"):
            send_elm_command(link, command)
            time.sleep(0.15)
        return [send_elm_command(link, command) for command in commands]


def obd_open_detail(config: dict[str, Any]) -> str:
    port = str(config.get("port", "")).strip()
    if port:
        return f"Opening serial ELM327 adapter {port} @ {int(config.get('baud') or config.get('baudrate') or 38400)} baud"
    return "Opening BLE ELM327 adapter"


def obd_live_detail(config: dict[str, Any]) -> str:
    port = str(config.get("port", "")).strip()
    if port:
        return f"OBD serial live on {port}"
    return "OBD BLE live"


def can_channel_label(config: dict[str, Any]) -> str:
    channel = str(config.get("channel", "")).strip() or "--"
    bitrate = config.get("bitrate", "")
    bitrate_text = f" @ {bitrate} bps" if bitrate not in (None, "") else ""
    listen_only = " listen-only" if bool(config.get("listenOnly", config.get("listen_only", False))) else ""
    return f"{channel}{bitrate_text}{listen_only}"


def can_open_detail(config: dict[str, Any]) -> str:
    return f"Opening CANable SLCAN channel {can_channel_label(config)}"


def no_can_frames_detail(config: dict[str, Any]) -> str:
    return (
        f"No CAN frames on {can_channel_label(config)}. "
        "Check IGN ON/engine running, OBD pin 6 CANH, pin 14 CANL, pin 4/5 GND, CANH/CANL swap, and bitrate."
    )
