from __future__ import annotations

from collections.abc import Callable
import os
from typing import Any, Protocol

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from .layout import color_tuple
from .warning_row_layout import WarningRowEntry, warning_row_entries


class BlitTarget(Protocol):
    def blit(self, surface: pygame.Surface, target: pygame.Rect) -> object:
        ...


def draw_warning_row_element(
    target: BlitTarget,
    element: dict[str, Any],
    *,
    rect: tuple[int, int, int, int],
    active_resolver: Callable[[str], Any],
    language: str,
    font_factory: Callable[[int, str, str, str], Any],
    scale_x: Callable[[float | int], int],
) -> None:
    entries = warning_row_entries(
        element.get("bindings", []),
        rect=rect,
        gap=scale_x(4),
        language=language,
    )
    if not entries:
        return
    draw_warning_row_entries(
        target,
        entries,
        active_resolver=active_resolver,
        active_color=color_tuple(element.get("color", "#ff0000")),
        inactive_color=color_tuple(element.get("inactive_color", "#666666")),
        font=font_factory(
            int(element.get("font_size", 22)),
            element.get("font_family", "default"),
            element.get("font_weight", "bold"),
            element.get("font_style", "normal"),
        ),
    )


def draw_warning_row_entries(
    target: BlitTarget,
    entries: tuple[WarningRowEntry, ...] | list[WarningRowEntry],
    *,
    active_resolver: Callable[[str], Any],
    active_color: tuple[int, int, int],
    inactive_color: tuple[int, int, int],
    font: Any,
) -> None:
    for entry in entries:
        active = bool(active_resolver(entry.binding))
        color = active_color if active else inactive_color
        lamp_rect = pygame.Rect(entry.rect)
        text_surface = font.render(entry.label, True, color)
        target.blit(text_surface, text_surface.get_rect(center=lamp_rect.center))
