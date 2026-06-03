from __future__ import annotations

import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame


def color_distance(left: pygame.Color, right: pygame.Color) -> int:
    return abs(left.r - right.r) + abs(left.g - right.g) + abs(left.b - right.b)


def tint_alpha_surface(source: pygame.Surface, color: tuple[int, int, int]) -> pygame.Surface:
    tinted = pygame.Surface(source.get_size(), pygame.SRCALPHA)
    width, height = source.get_size()
    background = source.get_at((0, 0))
    opaque_pixels = 0
    foreground_pixels = 0
    use_background_key = background.a > 0
    if use_background_key:
        for y in range(height):
            for x in range(width):
                pixel = source.get_at((x, y))
                if not pixel.a:
                    continue
                opaque_pixels += 1
                if color_distance(pixel, background) > 18:
                    foreground_pixels += 1
        use_background_key = opaque_pixels > 0 and foreground_pixels / opaque_pixels > 0.02
    for y in range(height):
        for x in range(width):
            pixel = source.get_at((x, y))
            alpha = pixel.a
            if not alpha:
                continue
            if use_background_key and color_distance(pixel, background) <= 18:
                continue
            tinted.set_at((x, y), (color[0], color[1], color[2], alpha))
    return tinted
