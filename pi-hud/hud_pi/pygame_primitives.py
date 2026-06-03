from __future__ import annotations

import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame


def draw_aa_arc(
    surface: pygame.Surface,
    color: tuple[int, int, int],
    center: tuple[int, int],
    radius: int,
    start_angle: float,
    end_angle: float,
    width: int,
) -> None:
    if end_angle <= start_angle:
        return
    upscale = 2
    rect = pygame.Rect(0, 0, (radius + width) * 2 * upscale, (radius + width) * 2 * upscale)
    temp = pygame.Surface(rect.size, pygame.SRCALPHA)
    temp_center = (rect.width // 2, rect.height // 2)
    temp_rect = pygame.Rect(
        temp_center[0] - radius * upscale,
        temp_center[1] - radius * upscale,
        radius * 2 * upscale,
        radius * 2 * upscale,
    )

    pygame.draw.arc(temp, color, temp_rect, start_angle, end_angle, width * upscale)

    scaled = pygame.transform.smoothscale(temp, (rect.width // upscale, rect.height // upscale))
    surface.blit(scaled, (center[0] - scaled.get_width() // 2, center[1] - scaled.get_height() // 2))
