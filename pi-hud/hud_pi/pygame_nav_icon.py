from __future__ import annotations

import math
import os
from collections.abc import Callable
from typing import Any

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from .nav_icon_geometry import arrow_head_segments, corner_arrow_shape, straight_arrow_segments, uturn_shape
from .nav_icon_state import nav_icon_presentation
from .surface_tint import tint_alpha_surface


def draw_nav_icon_element(
    surface: pygame.Surface,
    element: dict[str, Any],
    *,
    rect: tuple[int, int, int, int],
    resolve: Callable[[str, Any], Any],
    icon_loader: Callable[[str], pygame.Surface | None],
) -> None:
    presentation = nav_icon_presentation(element, resolve)
    icon = icon_loader(presentation.icon_name)
    if icon is not None:
        draw_nav_icon_surface(
            surface,
            icon,
            rect=rect,
            tint_color=presentation.draw_color,
        )
        return
    draw_nav_icon_fallback(
        surface,
        presentation.fallback_symbol,
        rect=rect,
        color=presentation.draw_color,
        destination_dot_color=presentation.destination_dot_color,
    )


def draw_nav_icon_surface(
    surface: pygame.Surface,
    icon: pygame.Surface,
    *,
    rect: tuple[int, int, int, int],
    tint_color: tuple[int, int, int],
) -> None:
    icon_rect = pygame.Rect(rect)
    scaled = pygame.transform.smoothscale(icon, (icon_rect.width, icon_rect.height))
    surface.blit(tint_alpha_surface(scaled, tint_color), icon_rect)


def draw_nav_icon_fallback(
    surface: pygame.Surface,
    symbol: str,
    *,
    rect: tuple[int, int, int, int],
    color: tuple[int, int, int],
    destination_dot_color: tuple[int, int, int],
) -> None:
    icon_rect = pygame.Rect(rect)
    line_width = max(3, min(icon_rect.width, icon_rect.height) // 10)
    if symbol == "destination":
        pygame.draw.circle(
            surface,
            color,
            icon_rect.center,
            max(6, min(icon_rect.width, icon_rect.height) // 5),
            width=line_width,
        )
        pygame.draw.circle(surface, destination_dot_color, icon_rect.center, max(2, line_width // 2))
        return
    if symbol == "roundabout":
        radius = max(8, min(icon_rect.width, icon_rect.height) // 4)
        pygame.draw.circle(surface, color, icon_rect.center, radius, width=line_width)
        _draw_arrow_head(surface, (icon_rect.centerx + radius, icon_rect.centery), "right", color, line_width)
        return
    if symbol == "uturn":
        _draw_uturn(surface, rect, color, line_width)
        return
    if symbol == "turn_right":
        _draw_corner_arrow(surface, rect, "right", color, line_width)
        return
    if symbol == "turn_left":
        _draw_corner_arrow(surface, rect, "left", color, line_width)
        return
    _draw_straight_arrow(surface, rect, color, line_width)


def _draw_straight_arrow(
    surface: pygame.Surface,
    rect: tuple[int, int, int, int],
    color: tuple[int, int, int],
    line_width: int,
) -> None:
    for start, end in straight_arrow_segments(rect):
        pygame.draw.line(surface, color, start, end, line_width)


def _draw_corner_arrow(
    surface: pygame.Surface,
    rect: tuple[int, int, int, int],
    direction: str,
    color: tuple[int, int, int],
    line_width: int,
) -> None:
    shape = corner_arrow_shape(rect, direction)
    pygame.draw.lines(surface, color, False, shape.polyline, line_width)
    for start, end in shape.head_segments:
        pygame.draw.line(surface, color, start, end, line_width)


def _draw_uturn(
    surface: pygame.Surface,
    rect: tuple[int, int, int, int],
    color: tuple[int, int, int],
    line_width: int,
) -> None:
    shape = uturn_shape(rect, line_width)
    pygame.draw.line(surface, color, shape.line_segment[0], shape.line_segment[1], line_width)
    pygame.draw.arc(surface, color, pygame.Rect(shape.arc_rect), math.radians(0), math.radians(180), line_width)
    for start, end in shape.head_segments:
        pygame.draw.line(surface, color, start, end, line_width)


def _draw_arrow_head(
    surface: pygame.Surface,
    point: tuple[int, int],
    direction: str,
    color: tuple[int, int, int],
    line_width: int,
) -> None:
    for start, end in arrow_head_segments(point, direction, line_width):
        pygame.draw.line(surface, color, start, end, line_width)
