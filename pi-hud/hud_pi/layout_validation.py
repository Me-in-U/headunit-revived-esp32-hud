from __future__ import annotations

from typing import Any

from .layout_canvas_validation import canvas_size, validate_canvas
from .layout_element_validation import (
    _validate_binding_shapes,
    _validate_element_bounds,
    _validate_element_colors,
    _validate_element_list,
    _validate_gear_config,
    _validate_value_config,
    validate_binding_shapes,
    validate_element_bounds,
    validate_element_colors,
    validate_element_list,
    validate_gear_config,
    validate_value_config,
)
from .layout_vehicle_validation import validate_vehicles


def validate_layout(layout: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    canvas = layout.get("canvas", {})
    width, height = canvas_size(canvas)
    errors.extend(validate_canvas(canvas))

    vehicles = layout.get("vehicles", [])
    vehicle_errors, vehicle_ids = validate_vehicles(vehicles)
    errors.extend(vehicle_errors)
    selected_vehicle = layout.get("selected_vehicle")
    if selected_vehicle and selected_vehicle not in vehicle_ids:
        errors.append(f"selected_vehicle '{selected_vehicle}' is not present in vehicles")

    dummy_data = layout.get("dummy_data", {})
    errors.extend(validate_element_list(layout.get("elements", []), dummy_data, width, height))
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
                errors.extend(validate_element_list(screen_elements, dummy_data, width, height))
    return errors


_validate_vehicles = validate_vehicles


__all__ = [
    "_validate_binding_shapes",
    "_validate_element_bounds",
    "_validate_element_colors",
    "_validate_element_list",
    "_validate_gear_config",
    "_validate_value_config",
    "_validate_vehicles",
    "validate_binding_shapes",
    "validate_canvas",
    "validate_element_bounds",
    "validate_element_colors",
    "validate_element_list",
    "validate_gear_config",
    "validate_layout",
    "validate_value_config",
    "validate_vehicles",
]
