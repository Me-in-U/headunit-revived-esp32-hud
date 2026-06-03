from __future__ import annotations

from typing import Any

from .layout_bindings import element_bindings, has_path
from .layout_element_common_validation import validate_binding_shapes, validate_element_bounds, validate_element_colors
from .layout_gear_validation import validate_gear_config
from .layout_schema import SUPPORTED_ELEMENT_TYPES
from .layout_value_validation import validate_value_config


def validate_element_list(elements: Any, dummy_data: dict[str, Any], canvas_width: int, canvas_height: int) -> list[str]:
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
        element_name = element_id or f"index {index}"
        errors.extend(validate_element_bounds(element, element_name, canvas_width, canvas_height))
        errors.extend(validate_element_colors(element, element_name))
        errors.extend(validate_binding_shapes(element, element_name))
        errors.extend(validate_value_config(element, element_name))
        errors.extend(validate_gear_config(element, element_name))
        for binding in element_bindings(element):
            if not has_path(dummy_data, binding):
                errors.append(f"element '{element_id}' binding '{binding}' has no dummy_data value")
    return errors


_validate_element_list = validate_element_list
_validate_element_bounds = validate_element_bounds
_validate_element_colors = validate_element_colors
_validate_binding_shapes = validate_binding_shapes
_validate_value_config = validate_value_config
_validate_gear_config = validate_gear_config
