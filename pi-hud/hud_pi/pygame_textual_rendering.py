from __future__ import annotations

from collections.abc import Callable
import os
from typing import Any, Protocol

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from .layout import color_tuple
from .pygame_text_rendering import draw_fitted_text, draw_value_with_unit
from .pygame_value_rendering import draw_value_style_element
from .textual_presentation import TextualRenderAction, textual_presentation, textual_render_action


class BlitTarget(Protocol):
    def blit(self, surface: pygame.Surface, target: pygame.Rect | tuple[int, int]) -> object:
        ...


def draw_textual_element(
    target: BlitTarget,
    element: dict[str, Any],
    *,
    resolve_first: Callable[[list[Any], Any], Any],
    rect: tuple[int, int, int, int],
    language: str,
    default_language: str,
    font_factory: Callable[[int, str, str, str], Any],
    scale_y: Callable[[float | int], int],
    scale_size: Callable[[float | int], int],
    fit_surface: Callable[[str, dict[str, Any], pygame.Rect, tuple[int, int, int]], pygame.Surface],
) -> TextualRenderAction | str:
    presentation = textual_presentation(element, resolve_first, language)
    action = textual_render_action(presentation)
    if action in {"bar", "analog", "needle", "sport_gauge"}:
        draw_value_style_element(
            target,
            element,
            raw_value=presentation.raw_value,
            value=presentation.value,
            rect=rect,
            style=action,
            font_factory=font_factory,
            scale_y=scale_y,
            scale_size=scale_size,
            language=language,
            default_language=default_language,
            fit_surface=fit_surface,
        )
        return action

    color = color_tuple(element.get("color", "#ffffff"))
    if presentation.uses_unit_layout:
        draw_value_with_unit(
            target,
            presentation.value,
            presentation.prefix,
            presentation.suffix,
            element,
            rect=rect,
            color=color,
            font_factory=font_factory,
            scale_size=scale_size,
        )
        return "unit"

    draw_fitted_text(
        target,
        presentation.text,
        element,
        rect=rect,
        color=color,
        fit_surface=fit_surface,
    )
    return "text"
