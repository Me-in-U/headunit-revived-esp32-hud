from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from hud_pi import pygame_value_bar
from hud_pi.pygame_value_bar import draw_value_bar_geometry
from hud_pi.value_bar_geometry import value_bar_geometry


class PygameValueBarTest(unittest.TestCase):
    def test_draw_value_bar_element_prepares_geometry_colors_and_scaled_border(self) -> None:
        surface = pygame.Surface((160, 80), pygame.SRCALPHA)
        element = {
            "inactive_color": "#102030",
            "accent": "#405060",
            "color": "#708090",
        }

        self.assertTrue(hasattr(pygame_value_bar, "draw_value_bar_element"))
        with patch("hud_pi.pygame_value_bar.draw_value_bar_geometry") as draw_geometry:
            pygame_value_bar.draw_value_bar_element(
                surface,
                element,
                rect=(10, 20, 120, 40),
                ratio=0.5,
                scale_y=lambda value: int(value * 2),
                scale_size=lambda value: int(value * 3),
            )

        args, kwargs = draw_geometry.call_args
        self.assertIs(surface, args[0])
        self.assertEqual(value_bar_geometry((10, 20, 120, 40), ratio=0.5, min_bar_height=20), args[1])
        self.assertEqual(
            {
                "track_color": (16, 32, 48),
                "fill_color": (64, 80, 96),
                "border_color": (112, 128, 144),
                "border_width": 3,
            },
            kwargs,
        )

    def test_draw_value_bar_geometry_draws_track_fill_segments_and_border(self) -> None:
        surface = pygame.Surface((160, 80), pygame.SRCALPHA)
        geometry = value_bar_geometry((10, 20, 120, 40), ratio=0.5, min_bar_height=10)

        with patch("hud_pi.pygame_value_bar.pygame.draw.rect", wraps=pygame.draw.rect) as draw_rect, patch(
            "hud_pi.pygame_value_bar.pygame.draw.line", wraps=pygame.draw.line
        ) as draw_line:
            draw_value_bar_geometry(
                surface,
                geometry,
                track_color=(26, 36, 48),
                fill_color=(36, 211, 107),
                border_color=(246, 251, 255),
                border_width=2,
            )

        self.assertGreaterEqual(draw_rect.call_count, 4)
        self.assertEqual(len(geometry.segment_lines), draw_line.call_count)


if __name__ == "__main__":
    unittest.main()
