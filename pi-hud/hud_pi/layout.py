from __future__ import annotations

import json
import copy
from pathlib import Path
from typing import Any

from .layout_schema import DEFAULT_GEARS, SUPPORTED_GEAR_STYLES, SUPPORTED_VALUE_STYLES
from .layout_validation import validate_layout
from .layout_values import (
    choice_or_default as _choice_or_default,
    clamp_int as _clamp_int,
    color_tuple,
    int_or_default as _int_or_default,
    number_or_default as _number_or_default,
    positive_int as _positive_int,
    string_or_default as _string_or_default,
)


def load_layout(path: str | Path) -> dict[str, Any]:
    layout_path = Path(path)
    with layout_path.open("r", encoding="utf-8") as handle:
        layout = json.load(handle)
    canvas = layout.setdefault("canvas", {})
    canvas.setdefault("width", 1920)
    canvas.setdefault("height", 480)
    canvas.setdefault("background", "#000000")
    layout.setdefault("elements", [])
    layout.setdefault("dummy_data", {})
    return layout


def normalize_layout_for_save(layout: dict[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(layout)
    canvas = normalized.setdefault("canvas", {})
    canvas["width"] = _positive_int(canvas.get("width"), 1920)
    canvas["height"] = _positive_int(canvas.get("height"), 480)
    canvas.setdefault("background", "#000000")
    normalized.setdefault("elements", [])
    normalized.setdefault("dummy_data", {})
    for index, element in enumerate(normalized["elements"]):
        normalize_element_for_canvas(element, canvas, index)
    screens = normalized.get("screens", {})
    if isinstance(screens, dict):
        for screen in screens.values():
            if not isinstance(screen, dict) or not isinstance(screen.get("elements"), list):
                continue
            for index, element in enumerate(screen["elements"]):
                if isinstance(element, dict):
                    normalize_element_for_canvas(element, canvas, index)
    return normalized


def normalize_element_for_canvas(element: dict[str, Any], canvas: dict[str, Any], z_fallback: int = 0) -> dict[str, Any]:
    width = _positive_int(canvas.get("width"), 1920)
    height = _positive_int(canvas.get("height"), 480)
    element["w"] = min(_positive_int(element.get("w"), 100), width)
    element["h"] = min(_positive_int(element.get("h"), 40), height)
    max_x = max(0, width - int(element["w"]))
    max_y = max(0, height - int(element["h"]))
    element["x"] = _clamp_int(element.get("x"), 0, max_x, 0)
    element["y"] = _clamp_int(element.get("y"), 0, max_y, 0)
    element["font_size"] = max(8, _int_or_default(element.get("font_size"), 28))
    element["font_family"] = _string_or_default(element.get("font_family"), "default")
    element["font_weight"] = _choice_or_default(element.get("font_weight"), {"normal", "bold"}, "normal")
    element["font_style"] = _choice_or_default(element.get("font_style"), {"normal", "italic"}, "normal")
    element["align"] = _choice_or_default(element.get("align"), {"left", "center", "right"}, "left")
    if element.get("type", "text") == "value":
        element["value_style"] = _choice_or_default(element.get("value_style"), SUPPORTED_VALUE_STYLES, "digital")
        if "min_value" in element:
            element["min_value"] = _number_or_default(element.get("min_value"), 0)
        if "max_value" in element:
            element["max_value"] = _number_or_default(element.get("max_value"), 100)
    elif element.get("type") == "gear_indicator":
        element.pop("value_style", None)
        element.pop("min_value", None)
        element.pop("max_value", None)
        element["gear_style"] = _choice_or_default(element.get("gear_style"), SUPPORTED_GEAR_STYLES, "strip")
        gears = element.get("gears")
        if not isinstance(gears, list) or not all(isinstance(item, str) and item.strip() for item in gears):
            element["gears"] = list(DEFAULT_GEARS)
        else:
            element["gears"] = [item.strip() for item in gears]
        element["active_font_size"] = max(
            int(element["font_size"]),
            _int_or_default(element.get("active_font_size"), int(element["font_size"]) * 2),
        )
    element["z"] = _int_or_default(element.get("z"), z_fallback)
    return element
