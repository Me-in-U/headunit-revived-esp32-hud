from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from hud_pi import pygame_nav_icon
from hud_pi.nav_icon_state import nav_icon_presentation
from hud_pi.pygame_nav_icon import draw_nav_icon_fallback, draw_nav_icon_surface


class PygameNavIconTest(unittest.TestCase):
    def test_draw_nav_icon_element_loads_icon_and_draws_presentation(self) -> None:
        surface = pygame.Surface((120, 120), pygame.SRCALPHA)
        icon = pygame.Surface((4, 4), pygame.SRCALPHA)
        element = {
            "event_binding": "nav.event_type",
            "side_binding": "nav.turn_side",
            "color": "#102030",
            "accent": "#405060",
            "inactive_color": "#708090",
        }
        values = {
            "nav.event_type": 4,
            "nav.turn_side": 2,
            "nav.connected": True,
        }
        loaded_icons: list[str] = []

        def resolve(binding: str, default: object) -> object:
            return values.get(binding, default)

        def icon_loader(icon_name: str) -> pygame.Surface | None:
            loaded_icons.append(icon_name)
            return icon

        presentation = nav_icon_presentation(element, resolve)
        self.assertTrue(hasattr(pygame_nav_icon, "draw_nav_icon_element"))
        with patch("hud_pi.pygame_nav_icon.draw_nav_icon_surface") as draw_surface, patch(
            "hud_pi.pygame_nav_icon.draw_nav_icon_fallback"
        ) as draw_fallback:
            pygame_nav_icon.draw_nav_icon_element(
                surface,
                element,
                rect=(10, 20, 32, 24),
                resolve=resolve,
                icon_loader=icon_loader,
            )

        self.assertEqual([presentation.icon_name], loaded_icons)
        self.assertEqual((surface, icon), draw_surface.call_args.args)
        self.assertEqual({"rect": (10, 20, 32, 24), "tint_color": presentation.draw_color}, draw_surface.call_args.kwargs)
        self.assertFalse(draw_fallback.called)

    def test_draw_nav_icon_surface_scales_tints_and_blits_icon(self) -> None:
        target = pygame.Surface((24, 24), pygame.SRCALPHA)
        icon = pygame.Surface((4, 4), pygame.SRCALPHA)
        icon.fill((255, 255, 255, 255))

        draw_nav_icon_surface(
            target,
            icon,
            rect=(5, 6, 10, 8),
            tint_color=(10, 20, 30),
        )

        self.assertEqual((0, 0, 0, 0), target.get_at((4, 6)))
        self.assertEqual((10, 20, 30, 255), target.get_at((9, 10)))

    def test_draw_nav_icon_fallback_destination_draws_outer_ring_and_center_dot(self) -> None:
        surface = pygame.Surface((120, 120), pygame.SRCALPHA)

        draw_nav_icon_fallback(
            surface,
            "destination",
            rect=(20, 20, 80, 80),
            color=(255, 255, 255),
            destination_dot_color=(36, 211, 107),
        )

        self.assertGreater(alpha_pixels(surface), 50)
        self.assertEqual((36, 211, 107, 255), surface.get_at((60, 60)))

    def test_draw_nav_icon_fallback_turn_and_uturn_symbols_draw_nonblank_shapes(self) -> None:
        for symbol in ("turn_right", "turn_left", "straight", "uturn", "roundabout"):
            with self.subTest(symbol=symbol):
                surface = pygame.Surface((120, 120), pygame.SRCALPHA)

                draw_nav_icon_fallback(
                    surface,
                    symbol,
                    rect=(20, 20, 80, 80),
                    color=(255, 255, 255),
                    destination_dot_color=(36, 211, 107),
                )

                self.assertGreater(alpha_pixels(surface), 20)


def alpha_pixels(surface: pygame.Surface) -> int:
    count = 0
    for x in range(surface.get_width()):
        for y in range(surface.get_height()):
            if surface.get_at((x, y)).a:
                count += 1
    return count


if __name__ == "__main__":
    unittest.main()
