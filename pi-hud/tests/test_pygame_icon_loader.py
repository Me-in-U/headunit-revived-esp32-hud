from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from hud_pi.pygame_icon_loader import load_cached_png_icon


class FakeSurface:
    def __init__(self, name: str, *, fail_convert: bool = False) -> None:
        self.name = name
        self.fail_convert = fail_convert

    def convert_alpha(self) -> "FakeSurface":
        if self.fail_convert:
            raise pygame.error("no display")
        return FakeSurface(f"{self.name}:converted")

    def copy(self) -> "FakeSurface":
        return FakeSurface(f"{self.name}:copy")


class PygameIconLoaderTest(unittest.TestCase):
    def test_load_cached_png_icon_cleans_name_and_caches_converted_surface(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            icon_dir = Path(temp_dir)
            (icon_dir / "turn_right.png").touch()
            cache: dict[str, FakeSurface] = {}

            with patch("hud_pi.pygame_icon_loader.pygame.image.load", return_value=FakeSurface("loaded")) as load:
                first = load_cached_png_icon(" Turn Right ", icon_dir, cache)
                second = load_cached_png_icon(" Turn Right ", icon_dir, cache)

        self.assertIs(first, second)
        self.assertEqual("loaded:converted", first.name)
        self.assertEqual("turn_right", next(iter(cache)))
        load.assert_called_once_with(str(icon_dir / "turn_right.png"))

    def test_load_cached_png_icon_returns_none_for_empty_or_missing_names(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            icon_dir = Path(temp_dir)
            cache: dict[str, FakeSurface] = {}

            self.assertIsNone(load_cached_png_icon("   ", icon_dir, cache))
            self.assertIsNone(load_cached_png_icon("missing", icon_dir, cache))

        self.assertEqual({}, cache)

    def test_load_cached_png_icon_copies_surface_when_alpha_conversion_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            icon_dir = Path(temp_dir)
            (icon_dir / "door_open.png").touch()
            cache: dict[str, FakeSurface] = {}

            with patch(
                "hud_pi.pygame_icon_loader.pygame.image.load",
                return_value=FakeSurface("loaded", fail_convert=True),
            ):
                loaded = load_cached_png_icon("door_open", icon_dir, cache)

        self.assertEqual("loaded:copy", loaded.name)


if __name__ == "__main__":
    unittest.main()
