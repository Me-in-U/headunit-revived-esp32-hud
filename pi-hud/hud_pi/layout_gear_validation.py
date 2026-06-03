from __future__ import annotations

from typing import Any

from .layout_schema import DEFAULT_GEARS, SUPPORTED_GEAR_STYLES
from .layout_values import int_or_default


def validate_gear_config(element: dict[str, Any], element_name: str) -> list[str]:
    if element.get("type", "text") != "gear_indicator":
        return []
    errors: list[str] = []
    gear_style = element.get("gear_style", "strip")
    if gear_style not in SUPPORTED_GEAR_STYLES:
        errors.append(f"element '{element_name}' gear_style '{gear_style}' is not supported")
    gears = element.get("gears", DEFAULT_GEARS)
    if not isinstance(gears, list):
        errors.append(f"element '{element_name}' gears must be a list of strings")
    else:
        for index, item in enumerate(gears):
            if not isinstance(item, str) or not item.strip():
                errors.append(f"element '{element_name}' gears[{index}] must be a non-empty string")
    active_font_size = element.get("active_font_size")
    if active_font_size is not None and int_or_default(active_font_size, -1) < 8:
        errors.append(f"element '{element_name}' active_font_size must be at least 8")
    return errors


_validate_gear_config = validate_gear_config
