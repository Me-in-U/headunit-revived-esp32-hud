from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from .gauge_values import gauge_angle_radians, numeric_value, polar_point


@dataclass(frozen=True)
class GaugeTickConfig:
    min_value: float
    max_value: float
    range_value: float
    interval: float
    count: int


@dataclass(frozen=True)
class GaugeTickEntry:
    inner: tuple[int, int]
    outer: tuple[int, int]
    is_major: bool
    line_width: int
    label: str | None
    label_pos: tuple[int, int] | None


@dataclass(frozen=True)
class SportGaugeTickEntry:
    inner: tuple[int, int]
    outer: tuple[int, int]
    is_major: bool
    is_redline: bool
    line_width: int
    label: str | None
    label_pos: tuple[int, int] | None


def gauge_tick_config(element: dict[str, Any]) -> GaugeTickConfig:
    min_value = numeric_value(element.get("min_value", 0)) or 0.0
    max_value = numeric_value(element.get("max_value", 100)) or 100.0
    range_value = max_value - min_value
    interval = numeric_value(element.get("tick_interval"))
    if not interval or interval <= 0:
        magnitude = 10 ** math.floor(math.log10(max(1, range_value)))
        if range_value / magnitude < 3:
            interval = magnitude / 5
        elif range_value / magnitude < 6:
            interval = magnitude / 2
        else:
            interval = magnitude
    return GaugeTickConfig(
        min_value=min_value,
        max_value=max_value,
        range_value=range_value,
        interval=interval,
        count=max(1, int(range_value / interval)),
    )


def gauge_tick_entries(
    element: dict[str, Any],
    *,
    center: tuple[int, int],
    radius: int,
    outer_ratio: float,
    major_inner_ratio: float,
    minor_inner_ratio: float,
    label_ratio: float,
) -> tuple[GaugeTickEntry, ...]:
    ticks = gauge_tick_config(element)
    entries: list[GaugeTickEntry] = []
    for tick in range(0, ticks.count + 1):
        tick_ratio = tick / ticks.count
        angle = gauge_angle_radians(tick_ratio)
        is_major = tick % 2 == 0 or tick == 0 or tick == ticks.count
        inner_ratio = major_inner_ratio if is_major else minor_inner_ratio
        outer = polar_point(center, radius * outer_ratio, angle)
        inner = polar_point(center, radius * inner_ratio, angle)
        label = None
        label_pos = None
        if is_major:
            tick_val = ticks.min_value + (tick * ticks.interval)
            label = f"{int(tick_val)}" if tick_val.is_integer() else f"{tick_val:.1f}"
            label_pos = polar_point(center, radius * label_ratio, angle)
        entries.append(
            GaugeTickEntry(
                inner=inner,
                outer=outer,
                is_major=is_major,
                line_width=2 if is_major else 1,
                label=label,
                label_pos=label_pos,
            )
        )
    return tuple(entries)


def sport_gauge_tick_entries(
    element: dict[str, Any],
    *,
    center: tuple[int, int],
    radius: int,
    sub_ticks: int = 4,
    label_ratio: float = 0.72,
) -> tuple[SportGaugeTickEntry, ...]:
    ticks = gauge_tick_config(element)
    minor_per_major = max(1, int(sub_ticks))
    total_ticks = ticks.count * minor_per_major
    entries: list[SportGaugeTickEntry] = []
    for tick in range(0, total_ticks + 1):
        tick_ratio = tick / total_ticks
        angle = gauge_angle_radians(tick_ratio)
        is_major = tick % minor_per_major == 0
        is_redline = tick_ratio >= 0.8
        tick_len = 0.12 if is_major else 0.05
        label = None
        label_pos = None
        if is_major:
            tick_val = ticks.min_value + (tick / minor_per_major * ticks.interval)
            if ticks.range_value >= 1000 and ticks.interval >= 500:
                display_val = tick_val / 1000
            else:
                display_val = tick_val
            label = f"{int(display_val)}" if display_val.is_integer() else f"{display_val:.1f}"
            label_pos = polar_point(center, radius * label_ratio, angle)
        entries.append(
            SportGaugeTickEntry(
                inner=polar_point(center, radius * (1.0 - tick_len), angle),
                outer=polar_point(center, radius, angle),
                is_major=is_major,
                is_redline=is_redline,
                line_width=3 if is_major else 1,
                label=label,
                label_pos=label_pos,
            )
        )
    return tuple(entries)
