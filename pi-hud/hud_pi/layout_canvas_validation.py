from __future__ import annotations

from typing import Any

from .layout_values import int_or_default, is_hex_color


def validate_canvas(canvas: Any) -> list[str]:
    errors: list[str] = []
    canvas_data = canvas if isinstance(canvas, dict) else {}
    width = int_or_default(canvas_data.get("width"), -1)
    height = int_or_default(canvas_data.get("height"), -1)
    if width <= 0 or height <= 0:
        errors.append("canvas width and height must be positive")
    background = canvas_data.get("background")
    if background is not None and not is_hex_color(background):
        errors.append(f"canvas background color '{background}' must be #RGB or #RRGGBB")
    return errors


def canvas_size(canvas: Any) -> tuple[int, int]:
    canvas_data = canvas if isinstance(canvas, dict) else {}
    return (
        int_or_default(canvas_data.get("width"), -1),
        int_or_default(canvas_data.get("height"), -1),
    )
