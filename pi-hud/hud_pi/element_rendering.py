from __future__ import annotations

from typing import Any, Literal


RenderAction = Literal["warning_row", "warning_icon", "nav_icon", "gear_indicator", "textual"]


def sorted_visible_elements(elements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        (element for element in elements if element.get("visible", True)),
        key=lambda item: item.get("z", 0),
    )


def render_action(element: dict[str, Any]) -> RenderAction:
    element_type = element.get("type", "text")
    if element_type == "warning_row":
        return "warning_row"
    if element_type == "warning_icon":
        return "warning_icon"
    if element_type == "nav_icon":
        return "nav_icon"
    if element_type == "gear_indicator":
        return "gear_indicator"
    return "textual"


def alpha_value(alpha: int) -> int:
    return max(0, min(255, alpha))
