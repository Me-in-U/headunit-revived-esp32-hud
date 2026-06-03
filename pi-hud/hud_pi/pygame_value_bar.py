from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from .layout import color_tuple
from .value_bar_geometry import ValueBarGeometry, value_bar_geometry, value_bar_highlight_color


def draw_value_bar_element(
    target: pygame.Surface,
    element: dict[str, Any],
    *,
    rect: tuple[int, int, int, int],
    ratio: float,
    scale_y: Callable[[float | int], int],
    scale_size: Callable[[float | int], int],
) -> None:
    track_color = color_tuple(element.get("inactive_color", "#1a2430"), (26, 36, 48))
    fill_color = color_tuple(element.get("accent", "#24d36b"), (36, 211, 107))
    border_color = color_tuple(element.get("color", "#f6fbff"), (246, 251, 255))
    geometry = value_bar_geometry(rect, ratio=ratio, min_bar_height=scale_y(10))
    draw_value_bar_geometry(
        target,
        geometry,
        track_color=track_color,
        fill_color=fill_color,
        border_color=border_color,
        border_width=max(1, scale_size(1)),
    )


def draw_value_bar_geometry(
    target: pygame.Surface,
    geometry: ValueBarGeometry,
    *,
    track_color: tuple[int, int, int],
    fill_color: tuple[int, int, int],
    border_color: tuple[int, int, int],
    border_width: int,
) -> None:
    bar_rect = pygame.Rect(geometry.bar_rect)
    pygame.draw.rect(target, track_color, bar_rect, border_radius=geometry.border_radius)

    if geometry.fill_rect is not None and geometry.highlight_rect is not None:
        fill_rect = pygame.Rect(geometry.fill_rect)
        pygame.draw.rect(target, fill_color, fill_rect, border_radius=geometry.border_radius)
        pygame.draw.rect(
            target,
            value_bar_highlight_color(fill_color),
            pygame.Rect(geometry.highlight_rect),
            border_radius=geometry.border_radius,
        )

    for start, end in geometry.segment_lines:
        pygame.draw.line(target, (0, 0, 0, 60), start, end, 1)

    pygame.draw.rect(target, border_color, bar_rect, width=border_width, border_radius=geometry.border_radius)
