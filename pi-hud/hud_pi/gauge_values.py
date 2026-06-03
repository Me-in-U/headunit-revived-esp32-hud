from __future__ import annotations

import math
from typing import Any


GAUGE_START_DEGREES = 135.0
GAUGE_SWEEP_DEGREES = 270.0


def numeric_value(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def value_ratio(raw_value: Any, *, min_value: Any = 0, max_value: Any = 100) -> float:
    numeric = numeric_value(raw_value)
    if numeric is None:
        return 0.0
    min_numeric = numeric_value(min_value)
    max_numeric = numeric_value(max_value)
    if min_numeric is None:
        min_numeric = 0.0
    if max_numeric is None or max_numeric <= min_numeric:
        max_numeric = min_numeric + 100.0
    return max(0.0, min(1.0, (numeric - min_numeric) / (max_numeric - min_numeric)))


def element_value_ratio(raw_value: Any, element: dict[str, Any]) -> float:
    return value_ratio(
        raw_value,
        min_value=element.get("min_value", 0),
        max_value=element.get("max_value", 100),
    )


def gauge_angle_degrees(ratio: float) -> float:
    clamped = max(0.0, min(1.0, ratio))
    return GAUGE_START_DEGREES + GAUGE_SWEEP_DEGREES * clamped


def gauge_angle_radians(ratio: float) -> float:
    return math.radians(gauge_angle_degrees(ratio))


def gauge_point(
    center: tuple[int, int],
    *,
    radius: int,
    ratio: float,
    length_ratio: float = 1.0,
) -> tuple[int, int]:
    return polar_point(center, radius * length_ratio, gauge_angle_radians(ratio))


def polar_point(center: tuple[int, int], length: float, angle: float) -> tuple[int, int]:
    return (
        center[0] + int(math.cos(angle) * length),
        center[1] + int(math.sin(angle) * length),
    )
