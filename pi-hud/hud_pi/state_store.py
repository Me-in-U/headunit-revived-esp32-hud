from __future__ import annotations

import copy
import time
from dataclasses import dataclass, field
from typing import Any

from .state_live_paths import (
    BRIDGE_SPEED_LIVE_VEHICLE_FIELDS,
    PI_OBD_LIVE_VEHICLE_FIELDS,
    live_paths_for_source,
    set_path_to_none,
)
from .state_merge import deep_merge, deep_merge_missing


_MISSING = object()


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
            deep_merge_missing(self.values, update)
        else:
            deep_merge(self.values, update)
        for path in live_paths_for_source(source, update):
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
            set_path_to_none(self.values, path)
            self.live_path_owners.pop(path, None)
