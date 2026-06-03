from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from hud_pi.gauge_geometry import sport_gauge_geometry, sport_gauge_needle_shape
from hud_pi import pygame_sport_gauge


class RecordingTarget:
    def __init__(self) -> None:
        self.blits: list[tuple[pygame.Surface, pygame.Rect]] = []

    def blit(self, surface: pygame.Surface, target: pygame.Rect) -> None:
        self.blits.append((surface, target.copy()))


class RecordingFont:
    def render(self, _text: str, _antialias: bool, _color: tuple[int, int, int]) -> pygame.Surface:
        return pygame.Surface((10, 6))


class PygameSportGaugeTest(unittest.TestCase):
    def test_sport_gauge_module_prepares_redline_ticks_and_pointer(self) -> None:
        target = RecordingTarget()
        font = RecordingFont()
        element = {
            "inactive_color": "#102030",
            "redline_color": "#405060",
            "color": "#708090",
            "font_size": 28,
            "font_family": "mono",
            "min_value": 0,
            "max_value": 8000,
        }
        scale_size = lambda value: int(value * 2)

        with patch("hud_pi.pygame_sport_gauge.draw_sport_gauge_arcs") as draw_arcs, patch(
            "hud_pi.pygame_sport_gauge.draw_sport_gauge_ticks"
        ) as draw_ticks, patch("hud_pi.pygame_sport_gauge.draw_sport_gauge_pointer") as draw_pointer:
            pygame_sport_gauge.draw_sport_gauge_element(
                target,  # type: ignore[arg-type]
                element,
                rect=(10, 20, 200, 100),
                ratio=0.5,
                font_factory=lambda _size, _family, _weight, _style: font,
                scale_size=scale_size,
            )

        center, radius = sport_gauge_geometry((10, 20, 200, 100))
        end, tail = sport_gauge_needle_shape(center=center, radius=radius, ratio=0.5)
        self.assertEqual({"center": center, "radius": radius, "track_color": (16, 32, 48), "redline_color": (64, 80, 96), "scale_width": scale_size}, draw_arcs.call_args.kwargs)
        self.assertEqual((64, 80, 96), draw_ticks.call_args.kwargs["redline_color"])
        self.assertEqual(end, draw_pointer.call_args.kwargs["end"])
        self.assertEqual(tail, draw_pointer.call_args.kwargs["tail"])


if __name__ == "__main__":
    unittest.main()
