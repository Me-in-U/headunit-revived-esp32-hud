from __future__ import annotations

import json
import copy
from pathlib import Path
from typing import Any


SUPPORTED_ELEMENT_TYPES = {"value", "text", "warning_row", "warning_icon", "nav_icon", "gear_indicator"}
SUPPORTED_VALUE_STYLES = {"digital", "bar", "analog", "needle", "sport_gauge"}
SUPPORTED_GEAR_STYLES = {"strip", "active_only"}
DEFAULT_GEARS = ["P", "R", "N", "D", "3", "2", "L"]


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


def color_tuple(value: str, fallback: tuple[int, int, int] = (255, 255, 255)) -> tuple[int, int, int]:
    if not isinstance(value, str) or not value.startswith("#") or len(value) not in (4, 7):
        return fallback
    try:
        if len(value) == 4:
            return tuple(int(ch * 2, 16) for ch in value[1:4])  # type: ignore[return-value]
        return tuple(int(value[index : index + 2], 16) for index in (1, 3, 5))  # type: ignore[return-value]
    except ValueError:
        return fallback


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


def validate_layout(layout: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    canvas = layout.get("canvas", {})
    width = _int_or_default(canvas.get("width"), -1)
    height = _int_or_default(canvas.get("height"), -1)
    if width <= 0 or height <= 0:
        errors.append("canvas width and height must be positive")
    background = canvas.get("background")
    if background is not None and not _is_hex_color(background):
        errors.append(f"canvas background color '{background}' must be #RGB or #RRGGBB")

    vehicles = layout.get("vehicles", [])
    vehicle_errors, vehicle_ids = _validate_vehicles(vehicles)
    errors.extend(vehicle_errors)
    selected_vehicle = layout.get("selected_vehicle")
    if selected_vehicle and selected_vehicle not in vehicle_ids:
        errors.append(f"selected_vehicle '{selected_vehicle}' is not present in vehicles")

    dummy_data = layout.get("dummy_data", {})
    errors.extend(_validate_element_list(layout.get("elements", []), dummy_data, width, height))
    screens = layout.get("screens")
    if screens is not None:
        if not isinstance(screens, dict):
            errors.append("screens must be an object")
        else:
            for screen_name, screen in screens.items():
                if not isinstance(screen, dict):
                    errors.append(f"screen '{screen_name}' must be an object")
                    continue
                screen_elements = screen.get("elements", [])
                if not isinstance(screen_elements, list):
                    errors.append(f"screen '{screen_name}' elements must be a list")
                    continue
                errors.extend(_validate_element_list(screen_elements, dummy_data, width, height))
    return errors


def _validate_element_list(elements: Any, dummy_data: dict[str, Any], canvas_width: int, canvas_height: int) -> list[str]:
    errors: list[str] = []
    if not isinstance(elements, list):
        return ["elements must be a list"]
    seen_ids: set[str] = set()
    for index, element in enumerate(elements):
        if not isinstance(element, dict):
            errors.append(f"element at index {index} must be an object")
            continue
        element_id = str(element.get("id", "")).strip()
        if not element_id:
            errors.append(f"element at index {index} is missing id")
        elif element_id in seen_ids:
            errors.append(f"duplicate element id '{element_id}'")
        else:
            seen_ids.add(element_id)

        element_type = element.get("type", "text")
        if element_type not in SUPPORTED_ELEMENT_TYPES:
            errors.append(f"element '{element_id}' type '{element_type}' is not supported")
        errors.extend(_validate_element_bounds(element, element_id or f"index {index}", canvas_width, canvas_height))
        errors.extend(_validate_element_colors(element, element_id or f"index {index}"))
        errors.extend(_validate_binding_shapes(element, element_id or f"index {index}"))
        errors.extend(_validate_value_config(element, element_id or f"index {index}"))
        errors.extend(_validate_gear_config(element, element_id or f"index {index}"))
        for binding in _element_bindings(element):
            if not _has_path(dummy_data, binding):
                errors.append(f"element '{element_id}' binding '{binding}' has no dummy_data value")
    return errors


def _validate_vehicles(vehicles: Any) -> tuple[list[str], set[str]]:
    errors: list[str] = []
    vehicle_ids: set[str] = set()
    if vehicles is None:
        return errors, vehicle_ids
    if not isinstance(vehicles, list):
        return ["vehicles must be a list"], vehicle_ids
    for index, vehicle in enumerate(vehicles):
        if not isinstance(vehicle, dict):
            errors.append(f"vehicle at index {index} must be an object")
            continue
        vehicle_id = str(vehicle.get("id", "")).strip()
        label = str(vehicle.get("label", "")).strip()
        if not vehicle_id:
            errors.append(f"vehicle at index {index} is missing id")
        elif vehicle_id in vehicle_ids:
            errors.append(f"duplicate vehicle id '{vehicle_id}'")
        else:
            vehicle_ids.add(vehicle_id)
        if not label:
            errors.append(f"vehicle at index {index} is missing label")
    return errors, vehicle_ids


def _validate_element_bounds(element: dict[str, Any], element_name: str, canvas_width: int, canvas_height: int) -> list[str]:
    errors: list[str] = []
    x = _int_or_default(element.get("x"), -1)
    y = _int_or_default(element.get("y"), -1)
    width = _int_or_default(element.get("w"), -1)
    height = _int_or_default(element.get("h"), -1)
    font_size = _int_or_default(element.get("font_size"), -1)
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


def _validate_element_colors(element: dict[str, Any], element_name: str) -> list[str]:
    errors: list[str] = []
    for key in ("color", "inactive_color", "accent", "active_color", "redline_color"):
        value = element.get(key)
        if value is not None and not _is_hex_color(value):
            errors.append(f"element '{element_name}' {key} '{value}' must be #RGB or #RRGGBB")
    return errors


def _validate_binding_shapes(element: dict[str, Any], element_name: str) -> list[str]:
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


def _validate_value_config(element: dict[str, Any], element_name: str) -> list[str]:
    if element.get("type", "text") != "value":
        return []
    errors: list[str] = []
    value_style = element.get("value_style", "digital")
    if value_style not in SUPPORTED_VALUE_STYLES:
        errors.append(f"element '{element_name}' value_style '{value_style}' is not supported")
    min_value = element.get("min_value")
    max_value = element.get("max_value")
    min_number = _maybe_number(min_value)
    max_number = _maybe_number(max_value)
    if min_value is not None and min_number is None:
        errors.append(f"element '{element_name}' min_value must be numeric")
    if max_value is not None and max_number is None:
        errors.append(f"element '{element_name}' max_value must be numeric")
    if min_number is not None and max_number is not None and max_number <= min_number:
        errors.append(f"element '{element_name}' max_value must be greater than min_value")
    return errors


def _validate_gear_config(element: dict[str, Any], element_name: str) -> list[str]:
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
    if active_font_size is not None and _int_or_default(active_font_size, -1) < 8:
        errors.append(f"element '{element_name}' active_font_size must be at least 8")
    return errors


def _element_bindings(element: dict[str, Any]) -> list[str]:
    bindings: list[str] = []
    fallback_bindings = element.get("fallback_bindings", [])
    if not isinstance(fallback_bindings, list):
        fallback_bindings = []
    for binding in [element.get("binding", "")] + fallback_bindings:
        if isinstance(binding, str) and binding.strip():
            bindings.append(binding.strip())
    row_bindings = element.get("bindings", [])
    if not isinstance(row_bindings, list):
        row_bindings = []
    for binding in row_bindings:
        if isinstance(binding, str) and binding.strip():
            bindings.append(binding.strip())
    for key in ("event_binding", "side_binding"):
        binding = element.get(key)
        if isinstance(binding, str) and binding.strip():
            bindings.append(binding.strip())
    return bindings


def _has_path(root: dict[str, Any], path: str) -> bool:
    node: Any = root
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return False
        node = node[part]
    return True


def _positive_int(value: Any, fallback: int) -> int:
    return max(1, _int_or_default(value, fallback))


def _clamp_int(value: Any, low: int, high: int, fallback: int) -> int:
    return min(high, max(low, _int_or_default(value, fallback)))


def _int_or_default(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _number_or_default(value: Any, fallback: float) -> int | float:
    number = _maybe_number(value)
    if number is None:
        return fallback
    return int(number) if number.is_integer() else number


def _maybe_number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _string_or_default(value: Any, fallback: str) -> str:
    if not isinstance(value, str) or not value.strip():
        return fallback
    return value.strip()


def _choice_or_default(value: Any, choices: set[str], fallback: str) -> str:
    if not isinstance(value, str):
        return fallback
    normalized = value.strip().lower()
    return normalized if normalized in choices else fallback


def _is_hex_color(value: Any) -> bool:
    if not isinstance(value, str) or not value.startswith("#") or len(value) not in (4, 7):
        return False
    try:
        int(value[1:], 16)
    except ValueError:
        return False
    return True
