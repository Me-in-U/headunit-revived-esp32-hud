from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .layout import color_tuple
from .navigation_icons import fallback_symbol, maneuver_icon_name


@dataclass(frozen=True)
class NavIconPresentation:
    event_type: int
    turn_side: int
    icon_name: str
    fallback_symbol: str
    active: bool
    draw_color: tuple[int, int, int]
    destination_dot_color: tuple[int, int, int]


def nav_icon_presentation(element: dict[str, Any], resolve: Callable[[str, Any], Any]) -> NavIconPresentation:
    event_type = _int_from_resolver(resolve, element.get("event_binding", "nav.event_type"), 0)
    turn_side = _int_from_resolver(resolve, element.get("side_binding", "nav.turn_side"), 3)
    active_color = color_tuple(element.get("color", "#f8fbff"), (248, 251, 255))
    accent = color_tuple(element.get("accent", "#1fd66f"), (31, 214, 111))
    inactive_color = color_tuple(element.get("inactive_color", "#53606a"), (83, 96, 106))
    active = bool(resolve("nav.connected", True))
    return NavIconPresentation(
        event_type=event_type,
        turn_side=turn_side,
        icon_name=maneuver_icon_name(event_type, turn_side),
        fallback_symbol=fallback_symbol(event_type, turn_side),
        active=active,
        draw_color=active_color if active else inactive_color,
        destination_dot_color=accent if active else inactive_color,
    )


def _int_from_resolver(resolve: Callable[[str, Any], Any], binding: Any, fallback: int) -> int:
    try:
        return int(resolve(str(binding), fallback))
    except (TypeError, ValueError):
        return fallback
