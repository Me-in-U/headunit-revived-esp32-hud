from __future__ import annotations

from typing import Any

from .layout_schema import SUPPORTED_VALUE_STYLES
from .layout_values import maybe_number


def validate_value_config(element: dict[str, Any], element_name: str) -> list[str]:
    if element.get("type", "text") != "value":
        return []
    errors: list[str] = []
    value_style = element.get("value_style", "digital")
    if value_style not in SUPPORTED_VALUE_STYLES:
        errors.append(f"element '{element_name}' value_style '{value_style}' is not supported")
    min_value = element.get("min_value")
    max_value = element.get("max_value")
    min_number = maybe_number(min_value)
    max_number = maybe_number(max_value)
    if min_value is not None and min_number is None:
        errors.append(f"element '{element_name}' min_value must be numeric")
    if max_value is not None and max_number is None:
        errors.append(f"element '{element_name}' max_value must be numeric")
    if min_number is not None and max_number is not None and max_number <= min_number:
        errors.append(f"element '{element_name}' max_value must be greater than min_value")
    return errors


_validate_value_config = validate_value_config
