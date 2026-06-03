from __future__ import annotations

from collections.abc import Callable
import math
import os
from typing import Any, Protocol

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from .gauge_geometry import (
    GAUGE_START_DEGREES,
    GAUGE_SWEEP_DEGREES,
    GaugeTickEntry,
    SportGaugeTickEntry,
)
from .pygame_primitives import draw_aa_arc


class BlitTarget(Protocol):
    def blit(self, surface: pygame.Surface, target: pygame.Rect) -> object:
        ...


def draw_gauge_progress_arcs(
    target: BlitTarget,
    *,
    center: tuple[int, int],
    radius: int,
    ratio: float,
    track_color: tuple[int, int, int],
    progress_color: tuple[int, int, int],
    width: int,
) -> None:
    start = GAUGE_START_DEGREES
    sweep = GAUGE_SWEEP_DEGREES
    clamped_ratio = max(0.0, min(1.0, ratio))
    draw_aa_arc(target, track_color, center, radius, math.radians(start), math.radians(start + sweep), width)
    draw_aa_arc(target, progress_color, center, radius, math.radians(start), math.radians(start + sweep * clamped_ratio), width)


def draw_sport_gauge_arcs(
    target: BlitTarget,
    *,
    center: tuple[int, int],
    radius: int,
    track_color: tuple[int, int, int],
    redline_color: tuple[int, int, int],
    scale_width: Callable[[float | int], int],
) -> None:
    start = GAUGE_START_DEGREES
    sweep = GAUGE_SWEEP_DEGREES
    draw_aa_arc(target, track_color, center, radius, math.radians(start), math.radians(start + sweep), max(2, scale_width(4)))
    draw_aa_arc(
        target,
        redline_color,
        center,
        int(radius * 0.88),
        math.radians(start + sweep * 0.8),
        math.radians(start + sweep),
        max(2, scale_width(4)),
    )


def draw_gauge_ticks(
    target: BlitTarget,
    entries: tuple[GaugeTickEntry, ...],
    *,
    color: tuple[int, int, int],
    font: Any,
    scale_width: Callable[[float | int], int],
) -> None:
    for tick in entries:
        pygame.draw.line(target, color, tick.inner, tick.outer, max(1, scale_width(tick.line_width)))
        if tick.label and tick.label_pos:
            text_surface = font.render(tick.label, True, color)
            target.blit(text_surface, text_surface.get_rect(center=tick.label_pos))


def draw_sport_gauge_ticks(
    target: BlitTarget,
    entries: tuple[SportGaugeTickEntry, ...],
    *,
    redline_color: tuple[int, int, int],
    major_color: tuple[int, int, int],
    minor_color: tuple[int, int, int],
    font: Any,
    scale_width: Callable[[float | int], int],
) -> None:
    for tick in entries:
        color = redline_color if tick.is_redline else (major_color if tick.is_major else minor_color)
        pygame.draw.line(target, color, tick.inner, tick.outer, max(1, scale_width(tick.line_width)))
        if tick.label and tick.label_pos:
            text_surface = font.render(tick.label, True, redline_color if tick.is_redline else major_color)
            target.blit(text_surface, text_surface.get_rect(center=tick.label_pos))


def draw_gauge_pointer(
    target: BlitTarget,
    *,
    center: tuple[int, int],
    end: tuple[int, int],
    accent_color: tuple[int, int, int],
    needle_color: tuple[int, int, int],
    scale_width: Callable[[float | int], int],
) -> None:
    pygame.draw.line(
        target,
        (0, 0, 0, 120),
        (center[0] + 2, center[1] + 2),
        (end[0] + 2, end[1] + 2),
        max(2, scale_width(6)),
    )
    pygame.draw.line(target, accent_color, center, end, max(3, scale_width(6)))
    pygame.draw.line(target, needle_color, center, end, max(1, scale_width(2)))
    pygame.draw.circle(target, needle_color, center, max(4, scale_width(8)))
    pygame.draw.circle(target, accent_color, center, max(2, scale_width(4)))


def draw_sport_gauge_pointer(
    target: BlitTarget,
    *,
    center: tuple[int, int],
    end: tuple[int, int],
    tail: tuple[int, int],
    redline_color: tuple[int, int, int],
    scale_width: Callable[[float | int], int],
) -> None:
    shadow_offset = max(1, scale_width(3))
    pygame.draw.line(
        target,
        (0, 0, 0, 150),
        (tail[0] + shadow_offset, tail[1] + shadow_offset),
        (end[0] + shadow_offset, end[1] + shadow_offset),
        max(2, scale_width(6)),
    )
    pygame.draw.line(target, redline_color, tail, end, max(2, scale_width(4)))
    pygame.draw.circle(target, (20, 25, 30), center, max(6, scale_width(16)))
    pygame.draw.circle(target, redline_color, center, max(4, scale_width(12)), max(1, scale_width(2)))
