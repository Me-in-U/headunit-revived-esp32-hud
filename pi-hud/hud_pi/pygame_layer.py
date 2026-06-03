from __future__ import annotations

from collections.abc import Callable
import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from .element_rendering import alpha_value


def render_alpha_layer(
    target: pygame.Surface,
    alpha: int,
    render_layer: Callable[[pygame.Surface], None],
) -> None:
    layer = pygame.Surface((target.get_width(), target.get_height()), pygame.SRCALPHA)
    render_layer(layer)
    layer.set_alpha(alpha_value(alpha))
    target.blit(layer, (0, 0))
