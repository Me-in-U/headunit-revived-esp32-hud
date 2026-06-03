from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from hud_pi.gauge_geometry import gauge_point, needle_gauge_geometry
from hud_pi import pygame_standard_gauge


class RecordingTarget:
    def __init__(self) -> None:
        self.blits: list[tuple[pygame.Surface, pygame.Rect]] = []

    def blit(self, surface: pygame.Surface, target: pygame.Rect) -> None:
        self.blits.append((surface, target.copy()))


class RecordingFont:
    def render(self, _text: str, _antialias: bool, _color: tuple[int, int, int]) -> pygame.Surface:
        return pygame.Surface((10, 6))


class PygameStandardGaugeTest(unittest.TestCase):
    def test_needle_gauge_module_prepares_geometry_ticks_and_pointer(self) -> None:
        target = RecordingTarget()
        font = RecordingFont()
        element = {
            "inactive_color": "#102030",
            "accent": "#405060",
            "color": "#708090",
            "font_size": 28,
            "font_family": "mono",
            "min_value": 0,
            "max_value": 220,
        }
        scale_size = lambda value: int(value * 2)

        with patch("hud_pi.pygame_standard_gauge.draw_gauge_progress_arcs") as draw_arcs, patch(
            "hud_pi.pygame_standard_gauge.draw_gauge_ticks"
        ) as draw_ticks, patch("hud_pi.pygame_standard_gauge.draw_gauge_pointer") as draw_pointer:
            pygame_standard_gauge.draw_needle_gauge_element(
                target,  # type: ignore[arg-type]
                element,
                rect=(10, 20, 200, 100),
                ratio=0.5,
                font_factory=lambda _size, _family, _weight, _style: font,
                scale_size=scale_size,
            )

        center, radius = needle_gauge_geometry((10, 20, 200, 100))
        self.assertEqual(radius, draw_arcs.call_args.kwargs["radius"])
        self.assertEqual({"color": (112, 128, 144), "font": font, "scale_width": scale_size}, draw_ticks.call_args.kwargs)
        self.assertEqual(
            gauge_point(center, radius=radius, ratio=0.5, length_ratio=0.85),
            draw_pointer.call_args.kwargs["end"],
        )


if __name__ == "__main__":
    unittest.main()
