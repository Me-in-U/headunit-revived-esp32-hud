from __future__ import annotations

from collections.abc import Callable
import os
from typing import Any, Protocol

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from .layout import color_tuple
from .text_layout import aligned_surface_rect, dimmed_unit_color, unit_font_size, value_label_rect, value_label_text, value_unit_positions


class BlitTarget(Protocol):
    def blit(self, surface: pygame.Surface, target: pygame.Rect | tuple[int, int]) -> object:
        ...


def draw_fitted_text(
    target: BlitTarget,
    text: str,
    element: dict[str, Any],
    *,
    rect: tuple[int, int, int, int],
    color: tuple[int, int, int],
    fit_surface: Callable[[str, dict[str, Any], pygame.Rect, tuple[int, int, int]], pygame.Surface],
) -> None:
    text_rect = pygame.Rect(rect)
    surface = fit_surface(text, element, text_rect, color)
    target_rect = pygame.Rect(
        aligned_surface_rect(
            rect,
            (surface.get_width(), surface.get_height()),
            str(element.get("align", "left")),
        )
    )
    target.blit(surface, target_rect)


def draw_value_with_unit(
    target: BlitTarget,
    value: str,
    prefix: str,
    suffix: str,
    element: dict[str, Any],
    *,
    rect: tuple[int, int, int, int],
    color: tuple[int, int, int],
    font_factory: Callable[[int, str, str, str], Any],
    scale_size: Callable[[float | int], int],
) -> None:
    requested_size = int(element.get("font_size", 28))
    unit_size = unit_font_size(requested_size)
    family = element.get("font_family", "default")
    weight = element.get("font_weight", "normal")
    style = element.get("font_style", "normal")

    value_font = font_factory(requested_size, family, "bold" if element.get("type") == "value" else weight, style)
    unit_font = font_factory(unit_size, family, weight, style)

    prefix_surface = value_font.render(prefix, True, color) if prefix else None
    value_surface = value_font.render(value, True, color)
    unit_surface = unit_font.render(suffix, True, dimmed_unit_color(color))
    positions = value_unit_positions(
        rect=rect,
        prefix_size=(prefix_surface.get_width(), prefix_surface.get_height()) if prefix_surface else None,
        value_size=(value_surface.get_width(), value_surface.get_height()),
        unit_size=(unit_surface.get_width(), unit_surface.get_height()),
        spacing=scale_size(4),
        align=str(element.get("align", "left")),
    )
    if prefix_surface:
        target.blit(prefix_surface, positions.prefix_pos)

    target.blit(value_surface, positions.value_pos)
    target.blit(unit_surface, positions.unit_pos)


def draw_value_label(
    target: BlitTarget,
    element: dict[str, Any],
    value: str,
    *,
    rect: tuple[int, int, int, int],
    y: int,
    language: str,
    default_language: str,
    color: tuple[int, int, int],
    fit_surface: Callable[[str, dict[str, Any], pygame.Rect, tuple[int, int, int]], pygame.Surface],
) -> None:
    text = value_label_text(element, value, language, default_language=default_language)
    label_rect = pygame.Rect(value_label_rect(rect, y=y))
    surface = fit_surface(text, element, label_rect, color)
    target.blit(surface, surface.get_rect(center=label_rect.center))


def draw_optional_value_label(
    target: BlitTarget,
    element: dict[str, Any],
    value: str,
    *,
    rect: tuple[int, int, int, int],
    style: str,
    language: str,
    default_language: str,
    fit_surface: Callable[[str, dict[str, Any], pygame.Rect, tuple[int, int, int]], pygame.Surface],
) -> bool:
    if not bool(element.get("show_value_label", False)):
        return False
    draw_value_label(
        target,
        element,
        value,
        rect=rect,
        y=value_label_y(rect, style),
        language=language,
        default_language=default_language,
        color=color_tuple(element.get("color", "#111111")),
        fit_surface=fit_surface,
    )
    return True


def value_label_y(rect: tuple[int, int, int, int], style: str) -> int:
    _rect_x, rect_y, _rect_w, rect_h = rect
    if style == "bar":
        return rect_y + max(0, rect_h // 12)
    if style == "sport_gauge":
        return rect_y + rect_h // 2 - max(16, rect_h // 10)
    return rect_y + rect_h - max(18, rect_h // 4)
