from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ScreenTransitionState:
    active_screen_name: str | None = None
    previous_screen_name: str | None = None
    transition_started_at: float = 0.0


def advance_screen_transition(
    state: ScreenTransitionState,
    next_screen_name: str,
    *,
    now: float,
) -> ScreenTransitionState:
    if state.active_screen_name is None:
        return ScreenTransitionState(
            active_screen_name=next_screen_name,
            previous_screen_name=state.previous_screen_name,
            transition_started_at=state.transition_started_at,
        )
    if state.active_screen_name == next_screen_name:
        return state
    return ScreenTransitionState(
        active_screen_name=next_screen_name,
        previous_screen_name=state.active_screen_name,
        transition_started_at=now,
    )


def active_screen_name(layout: dict[str, Any], *, nav_connected: bool) -> str:
    screens = layout.get("screens")
    if not isinstance(screens, dict) or not screens:
        return "default"
    if nav_connected and "bridge" in screens:
        return "bridge"
    if "standalone" in screens:
        return "standalone"
    return next(iter(screens))


def elements_for_screen(layout: dict[str, Any], screen_name: str | None) -> list[dict[str, Any]]:
    root_elements = layout.get("elements", [])
    if not screen_name or screen_name == "default":
        return list(root_elements)
    screens = layout.get("screens")
    if not isinstance(screens, dict):
        return list(root_elements)
    screen = screens.get(screen_name)
    if not isinstance(screen, dict):
        return list(root_elements)
    elements = screen.get("elements")
    return list(elements) if isinstance(elements, list) else list(root_elements)


def fade_duration_ms(layout: dict[str, Any]) -> int:
    transition = layout.get("screen_transition", {})
    if not isinstance(transition, dict) or transition.get("type", "fade") != "fade":
        return 0
    return int(transition.get("duration_ms", 0))


def fade_active(
    layout: dict[str, Any],
    *,
    previous_screen_name: str | None,
    transition_started_at: float,
    now: float,
) -> bool:
    if not previous_screen_name:
        return False
    duration_ms = fade_duration_ms(layout)
    if duration_ms <= 0:
        return False
    return (now - transition_started_at) * 1000 < duration_ms


def fade_progress(layout: dict[str, Any], *, transition_started_at: float, now: float) -> float:
    duration_ms = fade_duration_ms(layout)
    if duration_ms <= 0:
        return 1.0
    return max(0.0, min(1.0, ((now - transition_started_at) * 1000) / duration_ms))
