from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from hud_pi import pygame_gear_indicator
from hud_pi.gear_indicator import GearIndicatorEntry, gear_indicator_entries
from hud_pi.pygame_gear_indicator import draw_gear_indicator_entries


class RecordingTarget:
    def __init__(self) -> None:
        self.blits: list[tuple[pygame.Surface, pygame.Rect]] = []

    def blit(self, surface: pygame.Surface, target: pygame.Rect) -> None:
        self.blits.append((surface, target.copy()))


class RecordingFont:
    def __init__(self, rendered: list[tuple[str, tuple[int, int, int]]]) -> None:
        self.rendered = rendered

    def render(self, text: str, _antialias: bool, color: tuple[int, int, int]) -> pygame.Surface:
        self.rendered.append((text, color))
        return pygame.Surface((8, 6))


class PygameGearIndicatorTest(unittest.TestCase):
    def test_draw_gear_indicator_element_resolves_binding_and_draws_entries(self) -> None:
        target = RecordingTarget()
        element = {
            "binding": "vehicle.gear_range",
            "gear_style": "strip",
            "gears": ["P", "R", "N", "D"],
            "font_size": 20,
            "active_font_size": 36,
            "font_family": "mono",
            "font_weight": "normal",
            "font_style": "italic",
            "active_color": "#102030",
            "color": "#405060",
        }
        resolve_calls: list[tuple[str, object]] = []
        font_factory = lambda size, family, weight, style: RecordingFont([])

        def resolve(binding: str, default: object) -> object:
            resolve_calls.append((binding, default))
            return "D"

        self.assertTrue(hasattr(pygame_gear_indicator, "draw_gear_indicator_element"))
        with patch("hud_pi.pygame_gear_indicator.draw_gear_indicator_entries") as draw_entries:
            pygame_gear_indicator.draw_gear_indicator_element(
                target,  # type: ignore[arg-type]
                element,
                rect=(10, 20, 200, 40),
                resolve=resolve,
                font_factory=font_factory,
            )

        self.assertEqual([("vehicle.gear_range", "--")], resolve_calls)
        self.assertEqual((target, gear_indicator_entries(element, "D", rect=(10, 20, 200, 40))), draw_entries.call_args.args)
        self.assertEqual({"font_factory": font_factory}, draw_entries.call_args.kwargs)

    def test_draw_gear_indicator_entries_uses_entry_font_color_and_centering(self) -> None:
        target = RecordingTarget()
        rendered: list[tuple[str, tuple[int, int, int]]] = []
        font_calls: list[tuple[int, str, str, str]] = []

        def font_factory(size: int, family: str, weight: str, style: str) -> RecordingFont:
            font_calls.append((size, family, weight, style))
            return RecordingFont(rendered)

        draw_gear_indicator_entries(
            target,  # type: ignore[arg-type]
            (
                GearIndicatorEntry("P", (10, 20, 40, 20), 18, "Arial", "normal", "italic", (200, 200, 200)),
                GearIndicatorEntry("D", (50, 20, 40, 20), 44, "Arial", "bold", "italic", (36, 211, 107)),
            ),
            font_factory=font_factory,
        )

        self.assertEqual([(18, "Arial", "normal", "italic"), (44, "Arial", "bold", "italic")], font_calls)
        self.assertEqual([("P", (200, 200, 200)), ("D", (36, 211, 107))], rendered)
        self.assertEqual([(26, 27), (66, 27)], [rect.topleft for _surface, rect in target.blits])


if __name__ == "__main__":
    unittest.main()
