from __future__ import annotations

from typing import Any


def validate_vehicles(vehicles: Any) -> tuple[list[str], set[str]]:
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
