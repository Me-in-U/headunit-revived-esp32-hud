from __future__ import annotations

import math
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from hud_pi.pygame_gauge_primitives import draw_gauge_progress_arcs


class RecordingTarget:
    def blit(self, _surface: pygame.Surface, _target: pygame.Rect) -> None:
        pass


class PygameGaugePrimitivesTest(unittest.TestCase):
    def test_progress_arcs_preserve_track_and_clamped_progress_sweep(self) -> None:
        target = RecordingTarget()

        with patch("hud_pi.pygame_gauge_primitives.draw_aa_arc") as draw_arc:
            draw_gauge_progress_arcs(
                target,  # type: ignore[arg-type]
                center=(50, 60),
                radius=30,
                ratio=2.0,
                track_color=(1, 2, 3),
                progress_color=(4, 5, 6),
                width=6,
            )

        self.assertEqual(2, draw_arc.call_count)
        self.assertEqual((target, (1, 2, 3), (50, 60), 30, math.radians(135), math.radians(405), 6), draw_arc.call_args_list[0].args)
        self.assertEqual((target, (4, 5, 6), (50, 60), 30, math.radians(135), math.radians(405), 6), draw_arc.call_args_list[1].args)


if __name__ == "__main__":
    unittest.main()
