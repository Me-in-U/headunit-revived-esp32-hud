from __future__ import annotations

import unittest
import os
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from hud_pi.layout import load_layout
from hud_pi.renderer import HudRenderer
from hud_pi.state import HudState


EXPECTED_WARNING_LAMPS = [
    "door_open",
    "battery",
    "brake",
    "abs",
    "airbag",
    "oil_pressure",
    "check_engine",
    "eps",
    "coolant_temp",
]


class RecordingScreen:
    def __init__(self, width: int = 1920, height: int = 480) -> None:
        self.width = width
        self.height = height
        self.blits: list[tuple[pygame.Surface, pygame.Rect]] = []

    def get_width(self) -> int:
        return self.width

    def get_height(self) -> int:
        return self.height

    def blit(self, surface: pygame.Surface, target: pygame.Rect | tuple[int, int], **_kwargs: object) -> None:
        rect = target.copy() if isinstance(target, pygame.Rect) else surface.get_rect(topleft=target)
        self.blits.append((surface, rect))


class WarningIconTest(unittest.TestCase):
    def test_default_layout_uses_separate_warning_icon_elements(self) -> None:
        layout = load_layout("layouts/avante_hd_2010_default.json")
        warning_elements = [element for element in layout["elements"] if element.get("category") == "warnings"]
        icons = {element.get("icon"): element for element in warning_elements if element.get("type") == "warning_icon"}

        self.assertNotIn("warning_row", {element.get("type") for element in warning_elements})
        self.assertEqual(set(EXPECTED_WARNING_LAMPS), set(icons))
        for lamp, element in icons.items():
            self.assertEqual(f"warnings.{lamp}", element["binding"])
            self.assertFalse(element.get("show_when_inactive", False))

    def test_warning_icon_assets_are_transparent_pngs(self) -> None:
        icon_dir = Path("pi-hud/assets/warning-icons")
        missing: list[str] = []
        invalid: list[str] = []
        for lamp in EXPECTED_WARNING_LAMPS:
            path = icon_dir / f"{lamp}.png"
            if not path.exists():
                missing.append(lamp)
                continue
            surface = pygame.image.load(str(path))
            if surface.get_masks()[3] == 0:
                invalid.append(lamp)

        self.assertEqual([], missing)
        self.assertEqual([], invalid)

    def test_door_open_icon_uses_top_view_car_with_open_doors(self) -> None:
        surface = pygame.image.load("pi-hud/assets/warning-icons/door_open.png")

        self.assertGreater(alpha_pixels(surface, pygame.Rect(42, 14, 44, 100)), 420)
        self.assertGreater(alpha_pixels(surface, pygame.Rect(12, 50, 32, 56)), 130)
        self.assertGreater(alpha_pixels(surface, pygame.Rect(84, 50, 32, 56)), 130)
        self.assertLess(alpha_pixels(surface, pygame.Rect(56, 56, 16, 16)), 16)

    def test_warning_icon_is_hidden_until_bound_warning_is_active(self) -> None:
        screen = RecordingScreen()
        layout = {"canvas": {"width": 1920, "height": 480, "background": "#000000"}, "elements": []}
        renderer = HudRenderer(layout, screen)  # type: ignore[arg-type]
        icon = pygame.Surface((64, 64), pygame.SRCALPHA)
        icon.fill((255, 0, 0, 255))
        element = {
            "id": "door_open_icon",
            "type": "warning_icon",
            "icon": "door_open",
            "binding": "warnings.door_open",
            "x": 10,
            "y": 20,
            "w": 64,
            "h": 64,
            "show_when_inactive": False,
        }

        with patch.object(renderer, "_load_warning_icon", return_value=icon):
            renderer._draw_warning_icon(element, HudState({"warnings": {"door_open": False}}))
            self.assertEqual([], screen.blits)

            renderer._draw_warning_icon(element, HudState({"warnings": {"door_open": True}}))
            self.assertEqual(1, len(screen.blits))

    def test_active_warning_icon_blits_once_without_added_glow(self) -> None:
        screen = RecordingScreen()
        layout = {"canvas": {"width": 1920, "height": 480, "background": "#000000"}, "elements": []}
        renderer = HudRenderer(layout, screen)  # type: ignore[arg-type]
        icon = pygame.Surface((64, 64), pygame.SRCALPHA)
        icon.fill((255, 0, 0, 255))
        element = {
            "id": "brake_icon",
            "type": "warning_icon",
            "icon": "brake",
            "binding": "warnings.brake",
            "x": 10,
            "y": 20,
            "w": 64,
            "h": 64,
            "show_when_inactive": False,
        }

        with patch.object(renderer, "_load_warning_icon", return_value=icon):
            renderer._draw_warning_icon(element, HudState({"warnings": {"brake": True}}))

        self.assertEqual(1, len(screen.blits))

    def test_active_warning_icon_is_tinted_visible_when_source_icon_is_dark(self) -> None:
        screen = pygame.Surface((80, 80))
        screen.fill((0, 0, 0))
        layout = {"canvas": {"width": 80, "height": 80, "background": "#000000"}, "elements": []}
        renderer = HudRenderer(layout, screen)
        icon = pygame.Surface((64, 64), pygame.SRCALPHA)
        icon.fill((0, 0, 0, 255))
        element = {
            "id": "battery_icon",
            "type": "warning_icon",
            "icon": "battery",
            "binding": "warnings.battery",
            "x": 8,
            "y": 8,
            "w": 64,
            "h": 64,
            "color": "#ff2d2d",
            "accent": "#ff2d2d",
            "show_when_inactive": False,
        }

        with patch.object(renderer, "_load_warning_icon", return_value=icon):
            renderer._draw_warning_icon(element, HudState({"warnings": {"battery": True}}))

        changed_pixels = 0
        for x in range(screen.get_width()):
            for y in range(screen.get_height()):
                if screen.get_at((x, y))[:3] != (0, 0, 0):
                    changed_pixels += 1
        self.assertGreater(changed_pixels, 400)

    def test_active_warning_icon_uses_warning_color_even_when_layout_color_is_white(self) -> None:
        screen = pygame.Surface((80, 80))
        screen.fill((0, 0, 0))
        layout = {"canvas": {"width": 80, "height": 80, "background": "#000000"}, "elements": []}
        renderer = HudRenderer(layout, screen)
        icon = pygame.Surface((64, 64), pygame.SRCALPHA)
        icon.fill((0, 0, 0, 255))
        element = {
            "id": "check_engine_icon",
            "type": "warning_icon",
            "icon": "check_engine",
            "binding": "warnings.check_engine",
            "x": 8,
            "y": 8,
            "w": 64,
            "h": 64,
            "color": "#f6fbff",
            "accent": "#20d46b",
            "show_when_inactive": False,
        }

        with patch.object(renderer, "_load_warning_icon", return_value=icon):
            renderer._draw_warning_icon(element, HudState({"warnings": {"check_engine": True}}))

        sample = screen.get_at((40, 40))[:3]
        self.assertGreater(sample[0], 180)
        self.assertGreater(sample[1], 80)
        self.assertLess(sample[2], 80)

    def test_active_warning_icon_does_not_tint_solid_icon_background(self) -> None:
        screen = pygame.Surface((80, 80))
        screen.fill((0, 0, 0))
        layout = {"canvas": {"width": 80, "height": 80, "background": "#000000"}, "elements": []}
        renderer = HudRenderer(layout, screen)
        icon = pygame.Surface((64, 64), pygame.SRCALPHA)
        icon.fill((255, 255, 255, 255))
        pygame.draw.circle(icon, (0, 0, 0, 255), (32, 32), 18)
        element = {
            "id": "battery_icon",
            "type": "warning_icon",
            "icon": "battery",
            "binding": "warnings.battery",
            "x": 8,
            "y": 8,
            "w": 64,
            "h": 64,
            "color": "#f6fbff",
            "show_when_inactive": False,
        }

        with patch.object(renderer, "_load_warning_icon", return_value=icon):
            renderer._draw_warning_icon(element, HudState({"warnings": {"battery": True}}))

        self.assertEqual((0, 0, 0), screen.get_at((9, 9))[:3])
        self.assertGreater(screen.get_at((40, 40))[0], 180)

def alpha_pixels(surface: pygame.Surface, rect: pygame.Rect) -> int:
    count = 0
    clipped = rect.clip(surface.get_rect())
    for x in range(clipped.left, clipped.right):
        for y in range(clipped.top, clipped.bottom):
            if surface.get_at((x, y)).a:
                count += 1
    return count


if __name__ == "__main__":
    unittest.main()
