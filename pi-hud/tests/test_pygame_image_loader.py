from __future__ import annotations

import base64
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from hud_pi.pygame_image_loader import load_cached_image_source, load_pygame_image_source


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


class PygameImageLoaderTest(unittest.TestCase):
    def test_load_pygame_image_source_loads_file_paths_with_alpha_conversion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "background.png"
            path.touch()

            with patch("hud_pi.pygame_image_loader.pygame.image.load", return_value=FakeSurface("file")) as load:
                image = load_pygame_image_source(str(path))

        self.assertEqual("file:converted", image.name)
        load.assert_called_once_with(str(path))

    def test_load_pygame_image_source_loads_data_uri_bytes(self) -> None:
        source = "data:image/png;base64," + base64.b64encode(b"png-bytes").decode("ascii")

        with patch("hud_pi.pygame_image_loader.pygame.image.load", return_value=FakeSurface("data")) as load:
            image = load_pygame_image_source(source)

        self.assertEqual("data:converted", image.name)
        self.assertEqual(b"png-bytes", load.call_args.args[0].getvalue())

    def test_load_pygame_image_source_returns_none_for_missing_or_invalid_sources(self) -> None:
        self.assertIsNone(load_pygame_image_source(""))
        self.assertIsNone(load_pygame_image_source("missing-file.png"))
        self.assertIsNone(load_pygame_image_source("data:image/png;base64,%%%"))

    def test_load_pygame_image_source_copies_when_alpha_conversion_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "background.png"
            path.touch()

            with patch(
                "hud_pi.pygame_image_loader.pygame.image.load",
                return_value=FakeSurface("file", fail_convert=True),
            ):
                image = load_pygame_image_source(str(path))

        self.assertEqual("file:copy", image.name)

    def test_load_cached_image_source_reuses_matching_cache(self) -> None:
        cached = FakeSurface("cached")

        image, next_cache = load_cached_image_source(" background.png ", ("background.png", cached))

        self.assertIs(cached, image)
        self.assertEqual(("background.png", cached), next_cache)


if __name__ == "__main__":
    unittest.main()
