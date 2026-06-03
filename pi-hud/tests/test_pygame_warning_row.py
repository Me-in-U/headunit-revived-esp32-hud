from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from hud_pi import pygame_warning_row
from hud_pi.pygame_warning_row import draw_warning_row_entries
from hud_pi.warning_row_layout import WarningRowEntry, warning_row_entries


class RecordingTarget:
    def __init__(self) -> None:
        self.blits: list[tuple[pygame.Surface, pygame.Rect]] = []

    def blit(self, surface: pygame.Surface, target: pygame.Rect) -> None:
        self.blits.append((surface, target.copy()))


class RecordingFont:
    def __init__(self) -> None:
        self.rendered: list[tuple[str, tuple[int, int, int]]] = []

    def render(self, text: str, _antialias: bool, color: tuple[int, int, int]) -> pygame.Surface:
        self.rendered.append((text, color))
        return pygame.Surface((12, 8))


class PygameWarningRowTest(unittest.TestCase):
    def test_draw_warning_row_element_prepares_entries_colors_and_font(self) -> None:
        target = RecordingTarget()
        font = RecordingFont()
        element = {
            "bindings": ["warnings.door_open", "warnings.check_engine"],
            "color": "#102030",
            "inactive_color": "#405060",
            "font_size": 24,
            "font_family": "mono",
            "font_weight": "normal",
            "font_style": "italic",
        }
        font_requests: list[tuple[int, str, str, str]] = []

        def font_factory(size: int, family: str, weight: str, style: str) -> RecordingFont:
            font_requests.append((size, family, weight, style))
            return font

        self.assertTrue(hasattr(pygame_warning_row, "draw_warning_row_element"))
        with patch("hud_pi.pygame_warning_row.draw_warning_row_entries") as draw_entries:
            pygame_warning_row.draw_warning_row_element(
                target,  # type: ignore[arg-type]
                element,
                rect=(10, 20, 200, 40),
                active_resolver=lambda binding: binding == "warnings.door_open",
                language="en",
                font_factory=font_factory,
                scale_x=lambda value: int(value * 3),
            )

        self.assertEqual(
            (target, warning_row_entries(element["bindings"], rect=(10, 20, 200, 40), gap=12, language="en")),
            draw_entries.call_args.args,
        )
        self.assertEqual(
            {
                "active_resolver": draw_entries.call_args.kwargs["active_resolver"],
                "active_color": (16, 32, 48),
                "inactive_color": (64, 80, 96),
                "font": font,
            },
            draw_entries.call_args.kwargs,
        )
        self.assertEqual([(24, "mono", "normal", "italic")], font_requests)

    def test_draw_warning_row_entries_resolves_active_state_and_centers_labels(self) -> None:
        target = RecordingTarget()
        font = RecordingFont()
        active_bindings = {"warnings.door_open"}

        draw_warning_row_entries(
            target,  # type: ignore[arg-type]
            (
                WarningRowEntry("warnings.door_open", "DOOR", (10, 20, 40, 20)),
                WarningRowEntry("warnings.check_engine", "ENGINE", (50, 20, 40, 20)),
            ),
            active_resolver=lambda binding: binding in active_bindings,
            active_color=(255, 0, 0),
            inactive_color=(80, 80, 80),
            font=font,
        )

        self.assertEqual([("DOOR", (255, 0, 0)), ("ENGINE", (80, 80, 80))], font.rendered)
        self.assertEqual([(24, 26), (64, 26)], [rect.topleft for _surface, rect in target.blits])


if __name__ == "__main__":
    unittest.main()
