from __future__ import annotations

from typing import Any


PI_OBD_LIVE_VEHICLE_FIELDS = ("speed_kmh", "rpm", "coolant_c", "voltage_v")
PI_LOCAL_CANDIDATE_VEHICLE_FIELDS = ("fuel_percent", "gear_range", "gear_actual", "atf_c", "pedal_percent")
BRIDGE_SPEED_LIVE_VEHICLE_FIELDS = ("speed_kmh_backup",)
RUNTIME_LIVE_VEHICLE_FIELDS = (
    PI_OBD_LIVE_VEHICLE_FIELDS + PI_LOCAL_CANDIDATE_VEHICLE_FIELDS + BRIDGE_SPEED_LIVE_VEHICLE_FIELDS
)
CAN_STALE_EXCLUDED_PATHS = {"vehicle.can_state"}


def live_paths_for_source(source: str, update: dict[str, Any]) -> list[str]:
    if source == "obd":
        allowed = {f"vehicle.{field_name}" for field_name in PI_OBD_LIVE_VEHICLE_FIELDS}
        return [path for path in leaf_paths(update) if path in allowed]
    if source == "bridge_speed":
        allowed = {f"vehicle.{field_name}" for field_name in BRIDGE_SPEED_LIVE_VEHICLE_FIELDS}
        return [path for path in leaf_paths(update) if path in allowed]
    if source == "can":
        return [
            path
            for path in leaf_paths(update)
            if path not in CAN_STALE_EXCLUDED_PATHS and not path.startswith("debug.")
        ]
    return []


def leaf_paths(node: Any, prefix: str = "") -> list[str]:
    if not isinstance(node, dict):
        return []
    paths: list[str] = []
    for key, value in node.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        if value is None:
            continue
        if isinstance(value, dict):
            paths.extend(leaf_paths(value, path))
        else:
            paths.append(path)
    return paths


def set_path_to_none(values: dict[str, Any], path: str) -> None:
    parts = [part for part in path.split(".") if part]
    if not parts:
        return
    node: Any = values
    for part in parts[:-1]:
        if not isinstance(node, dict) or part not in node:
            return
        node = node[part]
    if isinstance(node, dict) and parts[-1] in node:
        node[parts[-1]] = None
