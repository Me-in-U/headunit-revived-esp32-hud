from __future__ import annotations

from collections.abc import Callable
import os
from typing import Any, Protocol

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from .gauge_geometry import element_value_ratio
from .pygame_gauge import draw_analog_gauge_element, draw_needle_gauge_element, draw_sport_gauge_element
from .pygame_text_rendering import draw_optional_value_label
from .pygame_value_bar import draw_value_bar_element


class BlitTarget(Protocol):
    def blit(self, surface: pygame.Surface, target: pygame.Rect | tuple[int, int]) -> object:
        ...


def draw_value_style_element(
    target: BlitTarget,
    element: dict[str, Any],
    *,
    raw_value: Any,
    value: str,
    rect: tuple[int, int, int, int],
    style: str,
    font_factory: Callable[[int, str, str, str], Any],
    scale_y: Callable[[float | int], int],
    scale_size: Callable[[float | int], int],
    language: str,
    default_language: str,
    fit_surface: Callable[[str, dict[str, Any], pygame.Rect, tuple[int, int, int]], pygame.Surface],
) -> bool:
    if rect[2] <= 0 or rect[3] <= 0:
        return False

    ratio = element_value_ratio(raw_value, element)
    if style == "bar":
        draw_value_bar_element(
            target,  # type: ignore[arg-type]
            element,
            rect=rect,
            ratio=ratio,
            scale_y=scale_y,
            scale_size=scale_size,
        )
    elif style == "analog":
        draw_analog_gauge_element(
            target,
            element,
            rect=rect,
            ratio=ratio,
            font_factory=font_factory,
            scale_size=scale_size,
        )
    elif style == "needle":
        draw_needle_gauge_element(
            target,
            element,
            rect=rect,
            ratio=ratio,
            font_factory=font_factory,
            scale_size=scale_size,
        )
    elif style == "sport_gauge":
        draw_sport_gauge_element(
            target,
            element,
            rect=rect,
            ratio=ratio,
            font_factory=font_factory,
            scale_size=scale_size,
        )
    else:
        return False

    draw_optional_value_label(
        target,
        element,
        value,
        rect=rect,
        style=style,
        language=language,
        default_language=default_language,
        fit_surface=fit_surface,
    )
    return True
