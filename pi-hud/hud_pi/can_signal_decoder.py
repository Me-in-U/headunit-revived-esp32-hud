from __future__ import annotations

from typing import Any

from .can_signal_profiles import is_confirmed_signal
from .can_signal_values import float_or_default, int_or_none, parse_frame_id


def decode_can_signals(frame_id: int, data: bytes, signals: list[dict[str, Any]]) -> dict[str, Any]:
    update: dict[str, Any] = {}
    for signal in signals:
        if not is_confirmed_signal(signal):
            continue
        if parse_frame_id(signal.get("frame_id")) != frame_id:
            continue
        decoded = decode_signal_value(data, signal)
        if decoded is None:
            continue
        set_path(update, str(signal["name"]), decoded)
    return update


def merge_nested_update(target: dict[str, Any], update: dict[str, Any]) -> None:
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            merge_nested_update(target[key], value)
        else:
            target[key] = value


def decode_signal_value(data: bytes, signal: dict[str, Any]) -> Any | None:
    if signal.get("bit_length") is not None:
        return decode_bit_signal_value(data, signal)
    return decode_byte_signal_value(data, signal)


def decode_byte_signal_value(data: bytes, signal: dict[str, Any]) -> Any | None:
    start = int_or_none(signal.get("start_byte"))
    length = int_or_none(signal.get("length"))
    if start is None or length is None or start < 0 or length <= 0:
        return None
    end = start + length
    if end > len(data):
        return None
    endian = "little" if signal.get("endian") == "little" else "big"
    signed = bool(signal.get("signed", False))
    raw = int.from_bytes(data[start:end], byteorder=endian, signed=signed)
    return map_and_scale_raw_value(raw, signal)


def decode_bit_signal_value(data: bytes, signal: dict[str, Any]) -> Any | None:
    start_byte = int_or_none(signal.get("start_byte"))
    start_bit = int_or_none(signal.get("start_bit"))
    bit_length = int_or_none(signal.get("bit_length"))
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
    return map_and_scale_raw_value(raw, signal)


def map_and_scale_raw_value(raw: int, signal: dict[str, Any]) -> Any:
    value_map = signal.get("value_map", {})
    if isinstance(value_map, dict):
        mapped = value_map.get(str(raw))
        if mapped is not None:
            return mapped
    scale = float_or_default(signal.get("scale"), 1.0)
    offset = float_or_default(signal.get("offset"), 0.0)
    decoded = raw * scale + offset
    if decoded.is_integer():
        return int(decoded)
    return round(decoded, 3)


def set_path(root: dict[str, Any], path: str, value: Any) -> None:
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


_decode_signal_value = decode_signal_value
_decode_byte_signal_value = decode_byte_signal_value
_decode_bit_signal_value = decode_bit_signal_value
_map_and_scale_raw_value = map_and_scale_raw_value
_set_path = set_path
