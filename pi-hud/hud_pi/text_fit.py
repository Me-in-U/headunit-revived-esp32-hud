from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pygame


FontFactory = Callable[[int, Any, Any, Any], Any]


def fit_text_surface(
    text: str,
    element: dict[str, Any],
    rect: pygame.Rect,
    color: tuple[int, int, int],
    font_factory: FontFactory,
) -> pygame.Surface:
    if rect.width <= 0 or rect.height <= 0:
        return pygame.Surface((0, 0), pygame.SRCALPHA)
    requested_size = int(element.get("font_size", 28))
    family = element.get("font_family", "default")
    weight = element.get("font_weight", "normal")
    style = element.get("font_style", "normal")
    min_size = 8
    for size in range(max(min_size, requested_size), min_size - 1, -1):
        surface = font_factory(size, family, weight, style).render(text, True, color)
        if surface.get_width() <= rect.width and surface.get_height() <= rect.height:
            return surface
    return ellipsized_surface(text, min_size, family, weight, style, rect, color, font_factory)


def ellipsized_surface(
    text: str,
    size: int,
    family: str,
    weight: str,
    style: str,
    rect: pygame.Rect,
    color: tuple[int, int, int],
    font_factory: FontFactory,
) -> pygame.Surface:
    font = font_factory(size, family, weight, style)
    if not text:
        return font.render("", True, color)
    ellipsis = "..."
    empty_surface = pygame.Surface((0, 0), pygame.SRCALPHA)
    ellipsis_surface = font.render(ellipsis, True, color)
    if ellipsis_surface.get_width() > rect.width or ellipsis_surface.get_height() > rect.height:
        return empty_surface
    for length in range(len(text), 0, -1):
        candidate = text[:length] + ellipsis
        surface = font.render(candidate, True, color)
        if surface.get_width() <= rect.width and surface.get_height() <= rect.height:
            return surface
    return empty_surface
