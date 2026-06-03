from __future__ import annotations

import importlib.util
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame


class PygameValueRenderingTest(unittest.TestCase):
    def test_draw_value_style_element_dispatches_bar_with_ratio_and_optional_label(self) -> None:
        self.assertIsNotNone(importlib.util.find_spec("hud_pi.pygame_value_rendering"))
        from hud_pi import pygame_value_rendering

        target = pygame.Surface((120, 80), pygame.SRCALPHA)
        element = {"min_value": 0, "max_value": 200, "show_value_label": True}
        font_factory = lambda size, family, weight, style: object()
        fit_surface = lambda text, fit_element, rect, color: pygame.Surface((10, 4))
        scale_y = lambda value: int(value * 2)
        scale_size = lambda value: int(value * 3)

        self.assertTrue(hasattr(pygame_value_rendering, "draw_value_style_element"))
        with patch("hud_pi.pygame_value_rendering.draw_value_bar_element") as draw_bar, patch(
            "hud_pi.pygame_value_rendering.draw_optional_value_label"
        ) as draw_label:
            result = pygame_value_rendering.draw_value_style_element(
                target,
                element,
                raw_value=100,
                value="100",
                rect=(10, 20, 80, 40),
                style="bar",
                font_factory=font_factory,
                scale_y=scale_y,
                scale_size=scale_size,
                language="en",
                default_language="en",
                fit_surface=fit_surface,
            )

        self.assertTrue(result)
        self.assertEqual((target, element), draw_bar.call_args.args)
        self.assertEqual(
            {
                "rect": (10, 20, 80, 40),
                "ratio": 0.5,
                "scale_y": scale_y,
                "scale_size": scale_size,
            },
            draw_bar.call_args.kwargs,
        )
        self.assertEqual((target, element, "100"), draw_label.call_args.args)
        self.assertEqual(
            {
                "rect": (10, 20, 80, 40),
                "style": "bar",
                "language": "en",
                "default_language": "en",
                "fit_surface": fit_surface,
            },
            draw_label.call_args.kwargs,
        )

    def test_draw_value_style_element_skips_invalid_rect(self) -> None:
        self.assertIsNotNone(importlib.util.find_spec("hud_pi.pygame_value_rendering"))
        from hud_pi import pygame_value_rendering

        target = pygame.Surface((120, 80), pygame.SRCALPHA)

        with patch("hud_pi.pygame_value_rendering.draw_value_bar_element") as draw_bar:
            result = pygame_value_rendering.draw_value_style_element(
                target,
                {},
                raw_value=100,
                value="100",
                rect=(10, 20, 0, 40),
                style="bar",
                font_factory=lambda size, family, weight, style: object(),
                scale_y=lambda value: int(value),
                scale_size=lambda value: int(value),
                language="en",
                default_language="en",
                fit_surface=lambda text, fit_element, rect, color: pygame.Surface((10, 4)),
            )

        self.assertFalse(result)
        draw_bar.assert_not_called()


if __name__ == "__main__":
    unittest.main()
