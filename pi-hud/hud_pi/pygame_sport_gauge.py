from __future__ import annotations

from collections.abc import Callable
import os
from typing import Any, Protocol

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from .gauge_geometry import sport_gauge_geometry, sport_gauge_needle_shape, sport_gauge_tick_entries
from .layout import color_tuple
from .pygame_gauge_primitives import draw_sport_gauge_arcs, draw_sport_gauge_pointer, draw_sport_gauge_ticks


class BlitTarget(Protocol):
    def blit(self, surface: pygame.Surface, target: pygame.Rect) -> object:
        ...


def draw_sport_gauge_element(
    target: BlitTarget,
    element: dict[str, Any],
    *,
    rect: tuple[int, int, int, int],
    ratio: float,
    font_factory: Callable[[int, str, str, str], Any],
    scale_size: Callable[[float | int], int],
) -> None:
    center, radius = sport_gauge_geometry(rect)

    track_color = color_tuple(element.get("inactive_color", "#1a2430"), (26, 36, 48))
    redline = color_tuple(element.get("redline_color", "#ff3b30"), (255, 59, 48))
    needle_color = color_tuple(element.get("color", "#f6fbff"), (246, 251, 255))

    draw_sport_gauge_arcs(
        target,
        center=center,
        radius=radius,
        track_color=track_color,
        redline_color=redline,
        scale_width=scale_size,
    )

    tick_font = font_factory(int(element.get("font_size", 28)) // 2 + 2, element.get("font_family", "default"), "bold", "normal")
    draw_sport_gauge_ticks(
        target,
        sport_gauge_tick_entries(element, center=center, radius=radius),
        redline_color=redline,
        major_color=needle_color,
        minor_color=track_color,
        font=tick_font,
        scale_width=scale_size,
    )

    end, tail = sport_gauge_needle_shape(center=center, radius=radius, ratio=ratio)
    draw_sport_gauge_pointer(
        target,
        center=center,
        end=end,
        tail=tail,
        redline_color=redline,
        scale_width=scale_size,
    )
