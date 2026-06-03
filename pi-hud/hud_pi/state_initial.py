from __future__ import annotations

from typing import Any

from .state_live_paths import RUNTIME_LIVE_VEHICLE_FIELDS
from .state_merge import clear_vehicle_fields
from .state_packets import inactive_navigation_update
from .state_store import HudState


def initial_vehicle_status_update(obd_configured: bool, can_configured: bool, dummy_enabled: bool) -> dict[str, Any]:
    return {
        "vehicle": {
            "source": "dummy" if dummy_enabled else "pi-local",
            "obd_state": "configured" if obd_configured else "not-configured",
            "can_state": "configured" if can_configured else "not-configured",
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
        clear_vehicle_fields(state.values, RUNTIME_LIVE_VEHICLE_FIELDS)
        state.merge("system", inactive_navigation_update())
    return state
