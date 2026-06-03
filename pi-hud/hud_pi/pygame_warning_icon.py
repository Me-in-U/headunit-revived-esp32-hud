from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any, Protocol

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from .surface_tint import tint_alpha_surface
from .warning_icon_state import warning_icon_presentation


class BlitTarget(Protocol):
    def blit(self, surface: pygame.Surface, target: pygame.Rect) -> object:
        ...


def draw_warning_icon_element(
    target: BlitTarget,
    element: dict[str, Any],
    *,
    rect: tuple[int, int, int, int],
    resolve: Callable[[str, Any], Any],
    icon_loader: Callable[[str], pygame.Surface | None],
) -> None:
    presentation = warning_icon_presentation(element, resolve)
    if not presentation.visible:
        return
    icon = icon_loader(presentation.icon_name)
    if icon is None:
        return
    draw_warning_icon_surface(
        target,
        icon,
        rect=rect,
        tint_color=presentation.tint_color,
        alpha=presentation.alpha,
    )


def draw_warning_icon_surface(
    target: BlitTarget,
    icon: pygame.Surface,
    *,
    rect: tuple[int, int, int, int],
    tint_color: tuple[int, int, int],
    alpha: int,
) -> None:
    target_rect = pygame.Rect(rect)
    scaled = pygame.transform.smoothscale(icon, (target_rect.width, target_rect.height))
    scaled = tint_alpha_surface(scaled, tint_color)
    if alpha != 255:
        scaled.set_alpha(alpha)
    target.blit(scaled, target_rect)
