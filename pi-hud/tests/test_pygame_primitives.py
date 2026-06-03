from __future__ import annotations

import math
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from hud_pi.pygame_primitives import draw_aa_arc


class PygamePrimitivesTest(unittest.TestCase):
    def test_draw_aa_arc_draws_scaled_arc_pixels_at_target_center(self) -> None:
        surface = pygame.Surface((96, 96), pygame.SRCALPHA)

        draw_aa_arc(surface, (255, 0, 0), (48, 48), 28, math.radians(0), math.radians(90), 4)

        self.assertGreater(alpha_pixels(surface), 20)

    def test_draw_aa_arc_skips_empty_arc_ranges(self) -> None:
        surface = pygame.Surface((96, 96), pygame.SRCALPHA)

        with patch("hud_pi.pygame_primitives.pygame.draw.arc", wraps=pygame.draw.arc) as draw_arc:
            draw_aa_arc(surface, (255, 0, 0), (48, 48), 28, math.radians(90), math.radians(0), 4)

        draw_arc.assert_not_called()
        self.assertEqual(0, alpha_pixels(surface))


def alpha_pixels(surface: pygame.Surface) -> int:
    count = 0
    for x in range(surface.get_width()):
        for y in range(surface.get_height()):
            if surface.get_at((x, y)).a:
                count += 1
    return count


if __name__ == "__main__":
    unittest.main()
