from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from hud_pi import pygame_text_rendering
from hud_pi.pygame_text_rendering import draw_fitted_text, draw_value_label, draw_value_with_unit


class RecordingTarget:
    def __init__(self) -> None:
        self.blits: list[tuple[pygame.Surface, pygame.Rect]] = []

    def blit(self, surface: pygame.Surface, target: pygame.Rect | tuple[int, int]) -> None:
        rect = target.copy() if isinstance(target, pygame.Rect) else surface.get_rect(topleft=target)
        self.blits.append((surface, rect))


class RecordingFont:
    def __init__(self, surfaces: dict[str, pygame.Surface], rendered: list[tuple[str, tuple[int, int, int]]]) -> None:
        self.surfaces = surfaces
        self.rendered = rendered

    def render(self, text: str, _antialias: bool, color: tuple[int, int, int]) -> pygame.Surface:
        self.rendered.append((text, color))
        return self.surfaces[text]


class PygameTextRenderingTest(unittest.TestCase):
    def test_draw_optional_value_label_uses_style_specific_y_and_color(self) -> None:
        target = RecordingTarget()
        element: dict[str, object] = {
            "show_value_label": True,
            "color": "#102030",
        }
        fit_surface = lambda text, fit_element, rect, color: pygame.Surface((10, 4))

        self.assertTrue(hasattr(pygame_text_rendering, "draw_optional_value_label"))
        with patch("hud_pi.pygame_text_rendering.draw_value_label") as draw_label:
            result = pygame_text_rendering.draw_optional_value_label(
                target,  # type: ignore[arg-type]
                element,  # type: ignore[arg-type]
                "72",
                rect=(20, 40, 100, 80),
                style="bar",
                language="en",
                default_language="en",
                fit_surface=fit_surface,  # type: ignore[arg-type]
            )

        self.assertTrue(result)
        self.assertEqual((target, element, "72"), draw_label.call_args.args)
        self.assertEqual(
            {
                "rect": (20, 40, 100, 80),
                "y": 46,
                "language": "en",
                "default_language": "en",
                "color": (16, 32, 48),
                "fit_surface": fit_surface,
            },
            draw_label.call_args.kwargs,
        )

    def test_draw_optional_value_label_skips_when_not_enabled(self) -> None:
        target = RecordingTarget()
        fit_surface = lambda text, fit_element, rect, color: pygame.Surface((10, 4))

        self.assertTrue(hasattr(pygame_text_rendering, "draw_optional_value_label"))
        with patch("hud_pi.pygame_text_rendering.draw_value_label") as draw_label:
            result = pygame_text_rendering.draw_optional_value_label(
                target,  # type: ignore[arg-type]
                {},
                "72",
                rect=(20, 40, 100, 80),
                style="sport_gauge",
                language="en",
                default_language="en",
                fit_surface=fit_surface,  # type: ignore[arg-type]
            )

        self.assertFalse(result)
        draw_label.assert_not_called()

    def test_draw_fitted_text_fits_and_blits_with_alignment_rules(self) -> None:
        target = RecordingTarget()
        fitted_surface = pygame.Surface((10, 4))
        fit_calls: list[tuple[str, dict[str, object], pygame.Rect, tuple[int, int, int]]] = []
        element: dict[str, object] = {"align": "center", "font_size": 24}

        def fit_surface(
            text: str,
            fit_element: dict[str, object],
            rect: pygame.Rect,
            color: tuple[int, int, int],
        ) -> pygame.Surface:
            fit_calls.append((text, fit_element, rect.copy(), color))
            return fitted_surface

        draw_fitted_text(
            target,  # type: ignore[arg-type]
            "READY",
            element,  # type: ignore[arg-type]
            rect=(20, 40, 100, 80),
            color=(1, 2, 3),
            fit_surface=fit_surface,  # type: ignore[arg-type]
        )

        self.assertEqual([("READY", element, pygame.Rect(20, 40, 100, 80), (1, 2, 3))], fit_calls)
        self.assertEqual([(65, 78)], [rect.topleft for _surface, rect in target.blits])

    def test_draw_value_label_builds_text_fits_surface_and_centers_label(self) -> None:
        target = RecordingTarget()
        fitted_surface = pygame.Surface((10, 4))
        fit_calls: list[tuple[str, dict[str, object], pygame.Rect, tuple[int, int, int]]] = []
        element: dict[str, object] = {
            "prefix": "RPM ",
            "suffix": " rpm",
            "font_size": 24,
        }

        def fit_surface(
            text: str,
            fit_element: dict[str, object],
            rect: pygame.Rect,
            color: tuple[int, int, int],
        ) -> pygame.Surface:
            fit_calls.append((text, fit_element, rect.copy(), color))
            return fitted_surface

        draw_value_label(
            target,  # type: ignore[arg-type]
            element,  # type: ignore[arg-type]
            "3",
            rect=(20, 40, 100, 80),
            y=60,
            language="en",
            default_language="en",
            color=(1, 2, 3),
            fit_surface=fit_surface,  # type: ignore[arg-type]
        )

        self.assertEqual(1, len(fit_calls))
        self.assertEqual("RPM 3 rpm", fit_calls[0][0])
        self.assertEqual(element, fit_calls[0][1])
        self.assertEqual(pygame.Rect(20, 60, 100, 26), fit_calls[0][2])
        self.assertEqual((1, 2, 3), fit_calls[0][3])
        self.assertEqual([(65, 71)], [rect.topleft for _surface, rect in target.blits])

    def test_draw_value_with_unit_uses_renderer_font_color_and_position_rules(self) -> None:
        target = RecordingTarget()
        surfaces = {
            "RPM ": pygame.Surface((30, 40)),
            "3": pygame.Surface((90, 40)),
            " x1000": pygame.Surface((50, 20)),
        }
        rendered: list[tuple[str, tuple[int, int, int]]] = []
        font_calls: list[tuple[int, str, str, str]] = []

        def font_factory(size: int, family: str, weight: str, style: str) -> RecordingFont:
            font_calls.append((size, family, weight, style))
            return RecordingFont(surfaces, rendered)

        draw_value_with_unit(
            target,  # type: ignore[arg-type]
            "3",
            "RPM ",
            " x1000",
            {"type": "value", "font_size": 40, "font_family": "Arial", "font_weight": "normal", "font_style": "italic", "align": "center"},
            rect=(100, 20, 300, 80),
            color=(100, 120, 140),
            font_factory=font_factory,
            scale_size=lambda value: int(value),
        )

        self.assertEqual(
            [(40, "Arial", "bold", "italic"), (20, "Arial", "normal", "italic")],
            font_calls,
        )
        self.assertEqual(
            [("RPM ", (100, 120, 140)), ("3", (100, 120, 140)), (" x1000", (60, 80, 100))],
            rendered,
        )
        self.assertEqual([(163, 40), (193, 40), (287, 50)], [rect.topleft for _surface, rect in target.blits])


if __name__ == "__main__":
    unittest.main()
