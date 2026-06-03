from __future__ import annotations

import copy
from typing import Any

from .can_signal_values import int_or_none, parse_frame_id


def selected_vehicle_can_signals(layout: dict[str, Any]) -> list[dict[str, Any]]:
    selected_vehicle = str(layout.get("selected_vehicle", "")).strip()
    for vehicle in layout.get("vehicles", []):
        if not isinstance(vehicle, dict) or vehicle.get("id") != selected_vehicle:
            continue
        signals = vehicle.get("can_signals", [])
        if not isinstance(signals, list):
            return []
        return [copy.deepcopy(signal) for signal in signals if is_confirmed_signal(signal)]
    return []


def is_confirmed_signal(signal: Any) -> bool:
    return (
        isinstance(signal, dict)
        and signal.get("confirmed") is True
        and parse_frame_id(signal.get("frame_id")) is not None
        and isinstance(signal.get("name"), str)
        and bool(signal.get("name", "").strip())
        and has_decodable_signal_shape(signal)
    )


def has_decodable_signal_shape(signal: dict[str, Any]) -> bool:
    if signal.get("bit_length") is not None:
        return (
            int_or_none(signal.get("start_byte")) is not None
            and int_or_none(signal.get("start_bit")) is not None
            and int_or_none(signal.get("bit_length")) is not None
        )
    return int_or_none(signal.get("start_byte")) is not None and int_or_none(signal.get("length")) is not None


_is_confirmed_signal = is_confirmed_signal
_has_decodable_signal_shape = has_decodable_signal_shape
