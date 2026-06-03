from __future__ import annotations

import copy
from typing import Any


def selected_vehicle_can_signals(layout: dict[str, Any]) -> list[dict[str, Any]]:
    selected_vehicle = str(layout.get("selected_vehicle", "")).strip()
    for vehicle in layout.get("vehicles", []):
        if not isinstance(vehicle, dict) or vehicle.get("id") != selected_vehicle:
            continue
        signals = vehicle.get("can_signals", [])
        if not isinstance(signals, list):
            return []
        return [copy.deepcopy(signal) for signal in signals if _is_confirmed_signal(signal)]
    return []


def decode_can_signals(frame_id: int, data: bytes, signals: list[dict[str, Any]]) -> dict[str, Any]:
    update: dict[str, Any] = {}
    for signal in signals:
        if not _is_confirmed_signal(signal):
            continue
        if _parse_frame_id(signal.get("frame_id")) != frame_id:
            continue
        decoded = _decode_signal_value(data, signal)
        if decoded is None:
            continue
        _set_path(update, str(signal["name"]), decoded)
    return update


def merge_nested_update(target: dict[str, Any], update: dict[str, Any]) -> None:
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            merge_nested_update(target[key], value)
        else:
            target[key] = value


def _is_confirmed_signal(signal: Any) -> bool:
    return (
        isinstance(signal, dict)
        and signal.get("confirmed") is True
        and _parse_frame_id(signal.get("frame_id")) is not None
        and isinstance(signal.get("name"), str)
        and bool(signal.get("name", "").strip())
        and _has_decodable_signal_shape(signal)
    )


def _decode_signal_value(data: bytes, signal: dict[str, Any]) -> Any | None:
    if signal.get("bit_length") is not None:
        return _decode_bit_signal_value(data, signal)
    return _decode_byte_signal_value(data, signal)


def _decode_byte_signal_value(data: bytes, signal: dict[str, Any]) -> Any | None:
    start = _int_or_none(signal.get("start_byte"))
    length = _int_or_none(signal.get("length"))
    if start is None or length is None or start < 0 or length <= 0:
        return None
    end = start + length
    if end > len(data):
        return None
    endian = "little" if signal.get("endian") == "little" else "big"
    signed = bool(signal.get("signed", False))
    raw = int.from_bytes(data[start:end], byteorder=endian, signed=signed)
    return _map_and_scale_raw_value(raw, signal)


def _decode_bit_signal_value(data: bytes, signal: dict[str, Any]) -> Any | None:
    start_byte = _int_or_none(signal.get("start_byte"))
    start_bit = _int_or_none(signal.get("start_bit"))
    bit_length = _int_or_none(signal.get("bit_length"))
    if start_byte is None or start_bit is None or bit_length is None:
        return None
    if start_byte < 0 or start_bit < 0 or start_bit > 7 or bit_length <= 0:
        return None
    absolute_bit = start_byte * 8 + start_bit
    if absolute_bit + bit_length > len(data) * 8:
        return None
    raw = 0
    for offset in range(bit_length):
        bit_index = absolute_bit + offset
        byte_value = data[bit_index // 8]
        bit_value = (byte_value >> (bit_index % 8)) & 0x01
        raw |= bit_value << offset
    return _map_and_scale_raw_value(raw, signal)


def _map_and_scale_raw_value(raw: int, signal: dict[str, Any]) -> Any:
    value_map = signal.get("value_map", {})
    if isinstance(value_map, dict):
        mapped = value_map.get(str(raw))
        if mapped is not None:
            return mapped
    scale = _float_or_default(signal.get("scale"), 1.0)
    offset = _float_or_default(signal.get("offset"), 0.0)
    decoded = raw * scale + offset
    if decoded.is_integer():
        return int(decoded)
    return round(decoded, 3)


def _set_path(root: dict[str, Any], path: str, value: Any) -> None:
    parts = [part for part in path.split(".") if part]
    if not parts:
        return
    node = root
    for part in parts[:-1]:
        child = node.get(part)
        if not isinstance(child, dict):
            child = {}
            node[part] = child
        node = child
    node[parts[-1]] = value


def _parse_frame_id(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return int(value, 0)
    except ValueError:
        return None


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float_or_default(value: Any, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _has_decodable_signal_shape(signal: dict[str, Any]) -> bool:
    if signal.get("bit_length") is not None:
        return (
            _int_or_none(signal.get("start_byte")) is not None
            and _int_or_none(signal.get("start_bit")) is not None
            and _int_or_none(signal.get("bit_length")) is not None
        )
    return _int_or_none(signal.get("start_byte")) is not None and _int_or_none(signal.get("length")) is not None
