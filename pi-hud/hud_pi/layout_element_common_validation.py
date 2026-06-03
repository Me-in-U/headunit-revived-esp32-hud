from __future__ import annotations

from typing import Any

from .layout_values import int_or_default, is_hex_color


def validate_element_bounds(element: dict[str, Any], element_name: str, canvas_width: int, canvas_height: int) -> list[str]:
    errors: list[str] = []
    x = int_or_default(element.get("x"), -1)
    y = int_or_default(element.get("y"), -1)
    width = int_or_default(element.get("w"), -1)
    height = int_or_default(element.get("h"), -1)
    font_size = int_or_default(element.get("font_size"), -1)
    if width <= 0 or height <= 0:
        errors.append(f"element '{element_name}' width and height must be positive")
    if x < 0 or y < 0:
        errors.append(f"element '{element_name}' x and y must be non-negative")
    if canvas_width > 0 and width > 0 and x + width > canvas_width:
        errors.append(f"element '{element_name}' exceeds canvas width")
    if canvas_height > 0 and height > 0 and y + height > canvas_height:
        errors.append(f"element '{element_name}' exceeds canvas height")
    if font_size < 8:
        errors.append(f"element '{element_name}' font_size must be at least 8")
    return errors


def validate_element_colors(element: dict[str, Any], element_name: str) -> list[str]:
    errors: list[str] = []
    for key in ("color", "inactive_color", "accent", "active_color", "redline_color"):
        value = element.get(key)
        if value is not None and not is_hex_color(value):
            errors.append(f"element '{element_name}' {key} '{value}' must be #RGB or #RRGGBB")
    return errors


def validate_binding_shapes(element: dict[str, Any], element_name: str) -> list[str]:
    errors: list[str] = []
    binding = element.get("binding")
    if binding is not None and not isinstance(binding, str):
        errors.append(f"element '{element_name}' binding must be a string")
    for key in ("fallback_bindings", "bindings"):
        value = element.get(key)
        if value is None:
            continue
        if not isinstance(value, list):
            errors.append(f"element '{element_name}' {key} must be a list of strings")
            continue
        for index, item in enumerate(value):
            if not isinstance(item, str):
                errors.append(f"element '{element_name}' {key}[{index}] must be a string")
    return errors


_validate_element_bounds = validate_element_bounds
_validate_element_colors = validate_element_colors
_validate_binding_shapes = validate_binding_shapes
