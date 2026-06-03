from __future__ import annotations

import os
import unittest

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from hud_pi.surface_tint import color_distance, tint_alpha_surface


class SurfaceTintTest(unittest.TestCase):
    def test_color_distance_uses_rgb_channels_only(self) -> None:
        self.assertEqual(60, color_distance(pygame.Color(10, 20, 30, 255), pygame.Color(30, 40, 50, 0)))

    def test_tint_alpha_surface_skips_solid_background_key_when_foreground_exists(self) -> None:
        source = pygame.Surface((10, 10), pygame.SRCALPHA)
        source.fill((255, 255, 255, 255))
        pygame.draw.rect(source, (0, 0, 0, 255), pygame.Rect(2, 2, 6, 6))

        tinted = tint_alpha_surface(source, (255, 0, 0))

        self.assertEqual(0, tinted.get_at((0, 0)).a)
        self.assertEqual((255, 0, 0, 255), tinted.get_at((5, 5)))

    def test_tint_alpha_surface_keeps_solid_dark_icon_without_background_key(self) -> None:
        source = pygame.Surface((10, 10), pygame.SRCALPHA)
        source.fill((0, 0, 0, 255))

        tinted = tint_alpha_surface(source, (255, 0, 0))

        self.assertEqual((255, 0, 0, 255), tinted.get_at((0, 0)))
        self.assertEqual((255, 0, 0, 255), tinted.get_at((5, 5)))


if __name__ == "__main__":
    unittest.main()
