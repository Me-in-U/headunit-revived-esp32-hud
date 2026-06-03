from __future__ import annotations


DESTINATION_EVENT_TYPES = {15}
ROUNDABOUT_EVENT_TYPES = {10, 11, 12}
STRAIGHT_EVENT_TYPES = {14}
UTURN_EVENT_TYPES = {6}


def maneuver_icon_name(event_type: int, turn_side: int) -> str:
    if event_type in DESTINATION_EVENT_TYPES:
        return "flag"
    if event_type in ROUNDABOUT_EVENT_TYPES:
        return "roundabout_left" if turn_side == 1 else "roundabout_right"
    if event_type in STRAIGHT_EVENT_TYPES:
        return "straight"
    if event_type in UTURN_EVENT_TYPES:
        return "u_turn_left" if turn_side == 1 else "u_turn_right"
    if turn_side == 2:
        return "turn_right"
    if turn_side == 1:
        return "turn_left"
    return "straight"


def fallback_symbol(event_type: int, turn_side: int) -> str:
    if event_type in DESTINATION_EVENT_TYPES:
        return "destination"
    if event_type in ROUNDABOUT_EVENT_TYPES:
        return "roundabout"
    if event_type in STRAIGHT_EVENT_TYPES:
        return "straight"
    if event_type in UTURN_EVENT_TYPES:
        return "uturn"
    if turn_side == 2:
        return "turn_right"
    if turn_side == 1:
        return "turn_left"
    return "straight"
