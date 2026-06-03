from __future__ import annotations

from collections.abc import Callable
import os
from typing import Any, Protocol

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from .gauge_geometry import analog_gauge_geometry, gauge_point, gauge_tick_entries, needle_gauge_geometry
from .layout import color_tuple
from .pygame_gauge_primitives import draw_gauge_pointer, draw_gauge_progress_arcs, draw_gauge_ticks


class BlitTarget(Protocol):
    def blit(self, surface: pygame.Surface, target: pygame.Rect) -> object:
        ...


def draw_analog_gauge_element(
    target: BlitTarget,
    element: dict[str, Any],
    *,
    rect: tuple[int, int, int, int],
    ratio: float,
    font_factory: Callable[[int, str, str, str], Any],
    scale_size: Callable[[float | int], int],
) -> None:
    center, radius = analog_gauge_geometry(rect)

    track_color = color_tuple(element.get("inactive_color", "#1a2430"), (26, 36, 48))
    accent = color_tuple(element.get("accent", "#24d36b"), (36, 211, 107))
    tick_color = color_tuple(element.get("color", "#f6fbff"), (246, 251, 255))

    draw_gauge_progress_arcs(
        target,
        center=center,
        radius=radius,
        ratio=ratio,
        track_color=track_color,
        progress_color=accent,
        width=max(2, scale_size(8)),
    )

    tick_font = font_factory(int(element.get("font_size", 28)) // 2, element.get("font_family", "default"), "normal", "normal")
    draw_gauge_ticks(
        target,
        gauge_tick_entries(
            element,
            center=center,
            radius=radius,
            outer_ratio=1.0,
            major_inner_ratio=0.82,
            minor_inner_ratio=0.90,
            label_ratio=0.70,
        ),
        color=tick_color,
        font=tick_font,
        scale_width=scale_size,
    )


def draw_needle_gauge_element(
    target: BlitTarget,
    element: dict[str, Any],
    *,
    rect: tuple[int, int, int, int],
    ratio: float,
    font_factory: Callable[[int, str, str, str], Any],
    scale_size: Callable[[float | int], int],
) -> None:
    center, radius = needle_gauge_geometry(rect)

    track_color = color_tuple(element.get("inactive_color", "#1a2430"), (26, 36, 48))
    accent = color_tuple(element.get("accent", "#24d36b"), (36, 211, 107))
    needle_color = color_tuple(element.get("color", "#f6fbff"), (246, 251, 255))

    draw_gauge_progress_arcs(
        target,
        center=center,
        radius=radius,
        ratio=ratio,
        track_color=track_color,
        progress_color=accent,
        width=max(2, scale_size(6)),
    )

    tick_font = font_factory(int(element.get("font_size", 28)) // 2, element.get("font_family", "default"), "normal", "normal")
    draw_gauge_ticks(
        target,
        gauge_tick_entries(
            element,
            center=center,
            radius=radius,
            outer_ratio=0.96,
            major_inner_ratio=0.84,
            minor_inner_ratio=0.88,
            label_ratio=0.72,
        ),
        color=needle_color,
        font=tick_font,
        scale_width=scale_size,
    )

    draw_gauge_pointer(
        target,
        center=center,
        end=gauge_point(center, radius=radius, ratio=ratio, length_ratio=0.85),
        accent_color=accent,
        needle_color=needle_color,
        scale_width=scale_size,
    )
