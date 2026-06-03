from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from hud_pi import pygame_warning_icon
from hud_pi.pygame_warning_icon import draw_warning_icon_surface


class RecordingTarget:
    def __init__(self) -> None:
        self.blits: list[tuple[pygame.Surface, pygame.Rect]] = []

    def blit(self, surface: pygame.Surface, target: pygame.Rect) -> None:
        self.blits.append((surface, target.copy()))


class PygameWarningIconTest(unittest.TestCase):
    def test_draw_warning_icon_element_loads_visible_icon_and_draws_presentation(self) -> None:
        target = RecordingTarget()
        icon = pygame.Surface((4, 4), pygame.SRCALPHA)
        loaded_icons: list[str] = []
        element = {
            "icon": "door",
            "binding": "warnings.door_open",
            "warning_color": "#102030",
            "inactive_color": "#405060",
        }

        def icon_loader(icon_name: str) -> pygame.Surface | None:
            loaded_icons.append(icon_name)
            return icon

        self.assertTrue(hasattr(pygame_warning_icon, "draw_warning_icon_element"))
        with patch("hud_pi.pygame_warning_icon.draw_warning_icon_surface") as draw_surface:
            pygame_warning_icon.draw_warning_icon_element(
                target,  # type: ignore[arg-type]
                element,
                rect=(10, 20, 32, 24),
                resolve=lambda binding, default: binding == "warnings.door_open",
                icon_loader=icon_loader,
            )

        self.assertEqual(["door"], loaded_icons)
        self.assertEqual((target, icon), draw_surface.call_args.args)
        self.assertEqual(
            {
                "rect": (10, 20, 32, 24),
                "tint_color": (16, 32, 48),
                "alpha": 255,
            },
            draw_surface.call_args.kwargs,
        )

    def test_draw_warning_icon_surface_scales_tints_applies_alpha_and_blits(self) -> None:
        target = RecordingTarget()
        icon = pygame.Surface((4, 4), pygame.SRCALPHA)
        icon.fill((0, 0, 0, 0))
        pygame.draw.circle(icon, (255, 255, 255, 255), (2, 2), 2)

        draw_warning_icon_surface(
            target,  # type: ignore[arg-type]
            icon,
            rect=(10, 20, 32, 24),
            tint_color=(255, 0, 0),
            alpha=80,
        )

        self.assertEqual(1, len(target.blits))
        surface, rect = target.blits[0]
        self.assertEqual((32, 24), surface.get_size())
        self.assertEqual(80, surface.get_alpha())
        self.assertEqual((10, 20), rect.topleft)


if __name__ == "__main__":
    unittest.main()
