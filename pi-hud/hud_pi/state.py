from __future__ import annotations

import copy
import time
from dataclasses import dataclass, field
from typing import Any


_MISSING = object()
PI_OBD_LIVE_VEHICLE_FIELDS = ("speed_kmh", "rpm", "coolant_c", "voltage_v")
PI_LOCAL_CANDIDATE_VEHICLE_FIELDS = ("fuel_percent", "gear_range", "gear_actual", "atf_c", "pedal_percent")
BRIDGE_SPEED_LIVE_VEHICLE_FIELDS = ("speed_kmh_backup",)
RUNTIME_LIVE_VEHICLE_FIELDS = (
    PI_OBD_LIVE_VEHICLE_FIELDS + PI_LOCAL_CANDIDATE_VEHICLE_FIELDS + BRIDGE_SPEED_LIVE_VEHICLE_FIELDS
)
CAN_STALE_EXCLUDED_PATHS = {"vehicle.can_state"}


def _deep_merge(target: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    for key, value in update.items():
        if value is None:
            continue
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_merge(target[key], value)
        else:
            target[key] = value
    return target


def _deep_merge_missing(target: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    for key, value in update.items():
        if value is None:
            continue
        if isinstance(value, dict):
            if not isinstance(target.get(key), dict):
                target[key] = copy.deepcopy(value)
            else:
                _deep_merge_missing(target[key], value)
            continue
        if key not in target or target[key] is None:
            target[key] = value
    return target


@dataclass
class HudState:
    values: dict[str, Any]
    updated_at: dict[str, float] = field(default_factory=dict)
    live_path_owners: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_layout(cls, layout: dict[str, Any]) -> "HudState":
        return cls(values=copy.deepcopy(layout.get("dummy_data", {})))

    def merge(self, source: str, update: dict[str, Any]) -> None:
        active_vehicle_source = self.resolve("vehicle.source", None)
        if source == "dummy" and active_vehicle_source not in (None, "dummy"):
            _deep_merge_missing(self.values, update)
        else:
            _deep_merge(self.values, update)
        for path in _live_paths_for_source(source, update):
            self.live_path_owners[path] = source
        self.updated_at[source] = time.monotonic()

    def resolve(self, path: str, fallback: Any = "--") -> Any:
        node: Any = self.values
        for part in path.split("."):
            if not isinstance(node, dict) or part not in node:
                return fallback
            node = node[part]
        if node is None:
            return fallback
        return node

    def resolve_first(self, paths: list[str], fallback: Any = "--") -> Any:
        for path in paths:
            value = self.resolve(path, _MISSING)
            if value is not _MISSING:
                return value
        return fallback

    def source_age_ms(self, source: str) -> int:
        timestamp = self.updated_at.get(source)
        if timestamp is None:
            return -1
        return int((time.monotonic() - timestamp) * 1000)

    def mark_stale_sources(self, stale_after_ms: int = 2500) -> None:
        for source, path in (("obd", ("vehicle", "obd_state")), ("can", ("vehicle", "can_state")), ("bridge_nav", ("nav", "connected"))):
            age = self.source_age_ms(source)
            if age < 0 or age <= stale_after_ms:
                continue
            if path[0] == "vehicle":
                self.values.setdefault("vehicle", {})[path[1]] = "stale"
                if source == "obd":
                    self._clear_owned_source_paths(
                        "obd",
                        {f"vehicle.{field_name}" for field_name in PI_OBD_LIVE_VEHICLE_FIELDS},
                    )
                elif source == "can":
                    self._clear_owned_source_paths("can")
            elif path[0] == "nav":
                self.values.setdefault("nav", {})[path[1]] = False
        bridge_speed_age = self.source_age_ms("bridge_speed")
        if bridge_speed_age > stale_after_ms:
            self._clear_owned_source_paths(
                "bridge_speed",
                {f"vehicle.{field_name}" for field_name in BRIDGE_SPEED_LIVE_VEHICLE_FIELDS},
            )

    def _clear_owned_source_paths(self, source: str, allowed_paths: set[str] | None = None) -> None:
        for path, owner in list(self.live_path_owners.items()):
            if owner != source:
                continue
            if allowed_paths is not None and path not in allowed_paths:
                continue
            _set_path_to_none(self.values, path)
            self.live_path_owners.pop(path, None)


def initial_vehicle_status_update(obd_configured: bool, can_configured: bool, dummy_enabled: bool) -> dict[str, Any]:
    return {
        "vehicle": {
            "source": "dummy" if dummy_enabled else "pi-local",
            "obd_state": "configured" if obd_configured else "not-configured",
            "can_state": "configured" if can_configured else "not-configured",
        }
    }


def inactive_navigation_update() -> dict[str, Any]:
    return {
        "nav": {
            "connected": False,
            "distance_meters": "--",
            "time_seconds": "--",
            "road": "",
            "instruction": "",
            "turn_side": "--",
            "event_type": "--",
        }
    }


def build_initial_state(layout: dict[str, Any], obd_configured: bool, can_configured: bool, dummy_enabled: bool) -> HudState:
    state = HudState.from_layout(layout)
    state.merge(
        "system",
        initial_vehicle_status_update(
            obd_configured=obd_configured,
            can_configured=can_configured,
            dummy_enabled=dummy_enabled,
        ),
    )
    if not dummy_enabled:
        _clear_vehicle_fields(state.values, RUNTIME_LIVE_VEHICLE_FIELDS)
        state.merge("system", inactive_navigation_update())
    return state


def normalize_packet(packet: dict[str, Any], allow_diagnostic_packets: bool = False) -> tuple[str, dict[str, Any]]:
    packet_type = packet.get("type", "navigation")
    if packet_type == "settings":
        return "settings", {}
    if packet_type == "speed":
        return "bridge_speed", {"vehicle": {"speed_kmh_backup": packet.get("speed_kmh")}}
    if packet_type == "vehicle_status":
        return "vehicle_status", {}
    if packet_type == "dtc_snapshot":
        if not allow_diagnostic_packets:
            return "ignored", {}
        return "dtc", {
            "dtc": {
                "stored": packet.get("stored", []),
                "pending": packet.get("pending", []),
                "permanent": packet.get("permanent", []),
                "count": len(packet.get("stored", [])) + len(packet.get("pending", [])),
            }
        }
    if packet_type == "vehicle_debug":
        if not allow_diagnostic_packets:
            return "ignored", {}
        return "debug", {
            "debug": {
                "can_frame_count": packet.get("can_frame_count"),
                "last_can_id": packet.get("last_can_id"),
                "obd_request": packet.get("obd_request"),
                "obd_response": packet.get("obd_response"),
            }
        }
    if packet_type != "navigation":
        return "ignored", {}
    if packet.get("active") is False:
        return "bridge_nav", inactive_navigation_update()
    return "bridge_nav", {
        "nav": {
            "connected": packet.get("active", True),
            "distance_meters": packet.get("distance_meters"),
            "time_seconds": packet.get("time_seconds"),
            "road": packet.get("road"),
            "instruction": packet.get("instruction") or packet.get("action_text"),
            "turn_side": packet.get("turn_side"),
            "event_type": packet.get("event_type", packet.get("next_event_type")),
        }
    }


def _clear_vehicle_fields(values: dict[str, Any], fields: tuple[str, ...]) -> None:
    vehicle = values.setdefault("vehicle", {})
    for field_name in fields:
        vehicle[field_name] = None


def _live_paths_for_source(source: str, update: dict[str, Any]) -> list[str]:
    if source == "obd":
        allowed = {f"vehicle.{field_name}" for field_name in PI_OBD_LIVE_VEHICLE_FIELDS}
        return [path for path in _leaf_paths(update) if path in allowed]
    if source == "bridge_speed":
        allowed = {f"vehicle.{field_name}" for field_name in BRIDGE_SPEED_LIVE_VEHICLE_FIELDS}
        return [path for path in _leaf_paths(update) if path in allowed]
    if source == "can":
        return [
            path
            for path in _leaf_paths(update)
            if path not in CAN_STALE_EXCLUDED_PATHS and not path.startswith("debug.")
        ]
    return []


def _leaf_paths(node: Any, prefix: str = "") -> list[str]:
    if not isinstance(node, dict):
        return []
    paths: list[str] = []
    for key, value in node.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        if value is None:
            continue
        if isinstance(value, dict):
            paths.extend(_leaf_paths(value, path))
        else:
            paths.append(path)
    return paths


def _set_path_to_none(values: dict[str, Any], path: str) -> None:
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
