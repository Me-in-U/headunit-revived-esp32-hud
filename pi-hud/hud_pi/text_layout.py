from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ValueUnitPositions:
    start_x: int
    total_width: int
    prefix_pos: tuple[int, int] | None
    value_pos: tuple[int, int]
    unit_pos: tuple[int, int]


def unit_font_size(requested_size: int) -> int:
    return max(12, requested_size // 2)


def dimmed_unit_color(color: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple(max(0, channel - 40) for channel in color)


def aligned_surface_rect(
    rect: tuple[int, int, int, int],
    surface_size: tuple[int, int],
    align: str,
) -> tuple[int, int, int, int]:
    rect_x, rect_y, rect_w, rect_h = rect
    surface_w, surface_h = surface_size
    y = rect_y + rect_h // 2 - surface_h // 2
    if align == "center":
        x = rect_x + rect_w // 2 - surface_w // 2
    elif align == "right":
        x = rect_x + rect_w - surface_w
    else:
        x = rect_x
    return (x, y, surface_w, surface_h)


def localized_element_text(
    element: dict[str, Any],
    key: str,
    language: str,
    fallback: Any = "",
    *,
    default_language: str = "en",
) -> str:
    translations = element.get(f"{key}_i18n")
    if isinstance(translations, dict):
        translated = translations.get(language)
        if translated is None:
            translated = translations.get(default_language)
        if translated is not None:
            return str(translated)
    return str(element.get(key, fallback))


def value_label_text(
    element: dict[str, Any],
    value: str,
    language: str,
    *,
    default_language: str = "en",
) -> str:
    prefix = localized_element_text(element, "prefix", language, "", default_language=default_language)
    suffix = localized_element_text(element, "suffix", language, "", default_language=default_language)
    return f"{prefix}{value}{suffix}"


def value_label_rect(rect: tuple[int, int, int, int], *, y: int) -> tuple[int, int, int, int]:
    x, _rect_y, width, height = rect
    return (x, y, width, max(1, height // 3))


def value_unit_positions(
    *,
    rect: tuple[int, int, int, int],
    prefix_size: tuple[int, int] | None,
    value_size: tuple[int, int],
    unit_size: tuple[int, int],
    spacing: int,
    align: str,
) -> ValueUnitPositions:
    rect_x, rect_y, rect_w, rect_h = rect
    prefix_w = prefix_size[0] if prefix_size else 0
    value_w, value_h = value_size
    unit_w, unit_h = unit_size
    total_width = prefix_w + value_w + unit_w + spacing

    if align == "center":
        start_x = rect_x + rect_w // 2 - total_width // 2
    elif align == "right":
        start_x = rect_x + rect_w - total_width
    else:
        start_x = rect_x

    center_y = rect_y + rect_h // 2
    value_y = center_y - value_h // 2
    unit_y = value_y + (value_h - unit_h) // 2
    value_x = start_x + prefix_w
    unit_x = value_x + value_w + spacing
    prefix_pos = (start_x, value_y) if prefix_size else None

    return ValueUnitPositions(
        start_x=start_x,
        total_width=total_width,
        prefix_pos=prefix_pos,
        value_pos=(value_x, value_y),
        unit_pos=(unit_x, unit_y),
    )
