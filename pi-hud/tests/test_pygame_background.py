from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from hud_pi import pygame_background
from hud_pi.pygame_background import draw_background_image


class PygameBackgroundTest(unittest.TestCase):
    def test_draw_canvas_background_fills_color_and_draws_fitted_image(self) -> None:
        target = pygame.Surface((120, 80), pygame.SRCALPHA)
        image = pygame.Surface((20, 20), pygame.SRCALPHA)
        canvas = {
            "background": "#102030",
            "background_image_fit": "contain",
        }

        self.assertTrue(hasattr(pygame_background, "draw_canvas_background"))
        with patch("hud_pi.pygame_background.draw_background_image") as draw_image:
            pygame_background.draw_canvas_background(target, canvas, image)

        self.assertEqual((16, 32, 48, 255), target.get_at((0, 0)))
        self.assertEqual((target, image), draw_image.call_args.args)
        self.assertEqual({"rect": (20, 0, 80, 80)}, draw_image.call_args.kwargs)

    def test_draw_background_image_scales_and_blits_to_target_rect(self) -> None:
        target = pygame.Surface((24, 24), pygame.SRCALPHA)
        image = pygame.Surface((2, 2), pygame.SRCALPHA)
        image.fill((12, 34, 56, 255))

        draw_background_image(target, image, rect=(5, 6, 10, 8))

        self.assertEqual((0, 0, 0, 0), target.get_at((4, 6)))
        self.assertEqual((12, 34, 56, 255), target.get_at((9, 10)))


if __name__ == "__main__":
    unittest.main()
