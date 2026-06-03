from __future__ import annotations

import importlib.util
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame


class PygameTextualRenderingTest(unittest.TestCase):
    def test_draw_textual_element_dispatches_value_style_renderer(self) -> None:
        self.assertIsNotNone(importlib.util.find_spec("hud_pi.pygame_textual_rendering"))
        from hud_pi import pygame_textual_rendering

        target = pygame.Surface((120, 80), pygame.SRCALPHA)
        element = {
            "type": "value",
            "binding": "vehicle.speed_kmh",
            "value_style": "needle",
        }
        font_factory = lambda size, family, weight, style: object()
        fit_surface = lambda text, fit_element, rect, color: pygame.Surface((10, 4))

        with patch("hud_pi.pygame_textual_rendering.draw_value_style_element") as draw_value_style:
            action = pygame_textual_rendering.draw_textual_element(
                target,
                element,
                resolve_first=lambda bindings, default: 72,
                rect=(10, 20, 80, 40),
                language="en",
                default_language="en",
                font_factory=font_factory,
                scale_y=lambda value: int(value),
                scale_size=lambda value: int(value),
                fit_surface=fit_surface,
            )

        self.assertEqual("needle", action)
        self.assertEqual((target, element), draw_value_style.call_args.args)
        self.assertEqual(
            {
                "raw_value": 72,
                "value": "72",
                "rect": (10, 20, 80, 40),
                "style": "needle",
                "font_factory": font_factory,
                "scale_y": draw_value_style.call_args.kwargs["scale_y"],
                "scale_size": draw_value_style.call_args.kwargs["scale_size"],
                "language": "en",
                "default_language": "en",
                "fit_surface": fit_surface,
            },
            draw_value_style.call_args.kwargs,
        )

    def test_draw_textual_element_draws_unit_layout_for_value_suffix(self) -> None:
        self.assertIsNotNone(importlib.util.find_spec("hud_pi.pygame_textual_rendering"))
        from hud_pi import pygame_textual_rendering

        target = pygame.Surface((120, 80), pygame.SRCALPHA)
        element = {
            "type": "value",
            "binding": "vehicle.voltage_v",
            "suffix": "V",
            "color": "#102030",
        }
        font_factory = lambda size, family, weight, style: object()

        with patch("hud_pi.pygame_textual_rendering.draw_value_with_unit") as draw_unit:
            action = pygame_textual_rendering.draw_textual_element(
                target,
                element,
                resolve_first=lambda bindings, default: 14.1,
                rect=(10, 20, 80, 40),
                language="en",
                default_language="en",
                font_factory=font_factory,
                scale_y=lambda value: int(value),
                scale_size=lambda value: int(value),
                fit_surface=lambda text, fit_element, rect, color: pygame.Surface((10, 4)),
            )

        self.assertEqual("unit", action)
        self.assertEqual((target, "14.1", "", "V", element), draw_unit.call_args.args)
        self.assertEqual(
            {
                "rect": (10, 20, 80, 40),
                "color": (16, 32, 48),
                "font_factory": font_factory,
                "scale_size": draw_unit.call_args.kwargs["scale_size"],
            },
            draw_unit.call_args.kwargs,
        )

    def test_draw_textual_element_draws_plain_fitted_text(self) -> None:
        self.assertIsNotNone(importlib.util.find_spec("hud_pi.pygame_textual_rendering"))
        from hud_pi import pygame_textual_rendering

        target = pygame.Surface((120, 80), pygame.SRCALPHA)
        element = {
            "type": "text",
            "text": "READY",
            "color": "#102030",
        }
        fit_surface = lambda text, fit_element, rect, color: pygame.Surface((10, 4))

        with patch("hud_pi.pygame_textual_rendering.draw_fitted_text") as draw_text:
            action = pygame_textual_rendering.draw_textual_element(
                target,
                element,
                resolve_first=lambda bindings, default: default,
                rect=(10, 20, 80, 40),
                language="en",
                default_language="en",
                font_factory=lambda size, family, weight, style: object(),
                scale_y=lambda value: int(value),
                scale_size=lambda value: int(value),
                fit_surface=fit_surface,
            )

        self.assertEqual("text", action)
        self.assertEqual((target, "READY", element), draw_text.call_args.args)
        self.assertEqual({"rect": (10, 20, 80, 40), "color": (16, 32, 48), "fit_surface": fit_surface}, draw_text.call_args.kwargs)


if __name__ == "__main__":
    unittest.main()
