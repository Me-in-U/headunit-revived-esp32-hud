from __future__ import annotations

from typing import Any


def parse_frame_id(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return int(value, 0)
    except ValueError:
        return None


def int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def float_or_default(value: Any, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


_parse_frame_id = parse_frame_id
_int_or_none = int_or_none
_float_or_default = float_or_default
