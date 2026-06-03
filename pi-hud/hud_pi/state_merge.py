from __future__ import annotations

import copy
from typing import Any


def deep_merge(target: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    for key, value in update.items():
        if value is None:
            continue
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            deep_merge(target[key], value)
        else:
            target[key] = value
    return target


def deep_merge_missing(target: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    for key, value in update.items():
        if value is None:
            continue
        if isinstance(value, dict):
            if not isinstance(target.get(key), dict):
                target[key] = copy.deepcopy(value)
            else:
                deep_merge_missing(target[key], value)
            continue
        if key not in target or target[key] is None:
            target[key] = value
    return target


def clear_vehicle_fields(values: dict[str, Any], fields: tuple[str, ...]) -> None:
    vehicle = values.setdefault("vehicle", {})
    for field_name in fields:
        vehicle[field_name] = None


_deep_merge = deep_merge
_deep_merge_missing = deep_merge_missing
_clear_vehicle_fields = clear_vehicle_fields
