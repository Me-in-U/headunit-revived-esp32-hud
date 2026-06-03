from __future__ import annotations

from typing import Any


def color_tuple(value: Any, fallback: tuple[int, int, int] = (255, 255, 255)) -> tuple[int, int, int]:
    if not isinstance(value, str) or not value.startswith("#") or len(value) not in (4, 7):
        return fallback
    try:
        if len(value) == 4:
            return tuple(int(ch * 2, 16) for ch in value[1:4])  # type: ignore[return-value]
        return tuple(int(value[index : index + 2], 16) for index in (1, 3, 5))  # type: ignore[return-value]
    except ValueError:
        return fallback


def is_hex_color(value: Any) -> bool:
    if not isinstance(value, str) or not value.startswith("#") or len(value) not in (4, 7):
        return False
    try:
        int(value[1:], 16)
    except ValueError:
        return False
    return True


def positive_int(value: Any, fallback: int) -> int:
    return max(1, int_or_default(value, fallback))


def clamp_int(value: Any, low: int, high: int, fallback: int) -> int:
    return min(high, max(low, int_or_default(value, fallback)))


def int_or_default(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def number_or_default(value: Any, fallback: float) -> int | float:
    number = maybe_number(value)
    if number is None:
        return fallback
    return int(number) if number.is_integer() else number


def maybe_number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def string_or_default(value: Any, fallback: str) -> str:
    if not isinstance(value, str) or not value.strip():
        return fallback
    return value.strip()


def choice_or_default(value: Any, choices: set[str], fallback: str) -> str:
    if not isinstance(value, str):
        return fallback
    normalized = value.strip().lower()
    return normalized if normalized in choices else fallback
