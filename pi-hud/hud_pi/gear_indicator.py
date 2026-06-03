from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .layout import color_tuple


DEFAULT_GEARS = ("P", "R", "N", "D", "3", "2", "L")


@dataclass(frozen=True)
class GearIndicatorEntry:
    label: str
    rect: tuple[int, int, int, int]
    font_size: int
    font_family: str
    font_weight: str
    font_style: str
    color: tuple[int, int, int]


def normalize_gears(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return DEFAULT_GEARS
    gears = tuple(str(gear).strip().upper() for gear in value if str(gear).strip())
    return gears or DEFAULT_GEARS


def normalize_active_gear(value: Any) -> str:
    return str(value if value is not None else "--").strip().upper() or "--"


def active_only_display(active: str) -> str:
    return active if active and active != "--" else "--"


def gear_indicator_entries(element: dict[str, Any], active_value: Any, *, rect: tuple[int, int, int, int]) -> tuple[GearIndicatorEntry, ...]:
    active = normalize_active_gear(active_value)
    style = str(element.get("gear_style", "strip"))
    active_color = color_tuple(element.get("active_color", element.get("accent", "#24d36b")), (36, 211, 107))
    inactive_color = color_tuple(element.get("inactive_color", "#4a5568"), (74, 85, 104))
    text_color = color_tuple(element.get("color", "#f6fbff"), (246, 251, 255))
    base_size = int(element.get("font_size", 28))
    active_size = int(element.get("active_font_size", max(base_size + 12, base_size * 2)))
    font_family = str(element.get("font_family", "default"))
    font_style = str(element.get("font_style", "normal"))

    if style == "active_only":
        display = active_only_display(active)
        return (
            GearIndicatorEntry(
                label=display,
                rect=rect,
                font_size=active_size,
                font_family=font_family,
                font_weight="bold",
                font_style=font_style,
                color=active_color if display != "--" else inactive_color,
            ),
        )

    x, y, width, height = rect
    gears = normalize_gears(element.get("gears"))
    slot_width = max(1, width // len(gears))
    entries = []
    for index, gear in enumerate(gears):
        is_active = gear == active
        entries.append(
            GearIndicatorEntry(
                label=gear,
                rect=(x + slot_width * index, y, slot_width, height),
                font_size=active_size if is_active else base_size,
                font_family=font_family,
                font_weight="bold" if is_active else str(element.get("font_weight", "normal")),
                font_style=font_style,
                color=active_color if is_active else text_color,
            )
        )
    return tuple(entries)
