from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .display_format import warning_active_color
from .layout import color_tuple


@dataclass(frozen=True)
class WarningIconPresentation:
    icon_name: str
    binding: str
    active: bool
    visible: bool
    tint_color: tuple[int, int, int]
    alpha: int


def warning_icon_presentation(
    element: dict[str, Any],
    resolve: Callable[[str, Any], Any],
) -> WarningIconPresentation:
    binding = str(element.get("binding", "")).strip()
    show_when_inactive = bool(element.get("show_when_inactive", False))
    active = bool(resolve(binding, False)) if binding else show_when_inactive
    visible = active or show_when_inactive
    active_color = element.get("warning_color", warning_active_color(binding))
    inactive_color = element.get("inactive_color", "#4a5568")
    return WarningIconPresentation(
        icon_name=str(element.get("icon", element.get("id", ""))),
        binding=binding,
        active=active,
        visible=visible,
        tint_color=color_tuple(
            active_color if active else inactive_color,
            (255, 59, 48) if active else (74, 85, 104),
        ),
        alpha=255 if active else int(element.get("inactive_alpha", 80)),
    )
