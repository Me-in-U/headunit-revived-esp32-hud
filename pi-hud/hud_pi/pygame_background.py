from __future__ import annotations

import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from .background_layout import background_target_rect
from .layout import color_tuple


def draw_canvas_background(
    surface: pygame.Surface,
    canvas: dict[str, object],
    image: pygame.Surface | None,
) -> None:
    surface.fill(color_tuple(canvas.get("background", "#000000"), (0, 0, 0)))
    if image is None:
        return
    rect = background_target_rect(
        (surface.get_width(), surface.get_height()),
        (image.get_width(), image.get_height()),
        str(canvas.get("background_image_fit", "cover")),
    )
    draw_background_image(surface, image, rect=rect)


def draw_background_image(
    surface: pygame.Surface,
    image: pygame.Surface,
    *,
    rect: tuple[int, int, int, int],
) -> None:
    target_rect = pygame.Rect(rect)
    scaled = pygame.transform.smoothscale(image, (target_rect.width, target_rect.height))
    surface.blit(scaled, target_rect)
