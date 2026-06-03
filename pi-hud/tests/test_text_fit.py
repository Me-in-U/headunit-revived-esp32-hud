from __future__ import annotations

import os
import unittest

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from hud_pi.text_fit import ellipsized_surface, fit_text_surface


class FakeFont:
    def __init__(self, size: int) -> None:
        self.size = size

    def render(self, text: str, _antialias: bool, _color: tuple[int, int, int]) -> pygame.Surface:
        return pygame.Surface((max(1, len(text) * self.size), max(1, self.size)))


class TextFitTest(unittest.TestCase):
    def test_fit_text_surface_shrinks_until_text_fits_rect(self) -> None:
        requested: list[int] = []

        def font_factory(size: int, *_args: object) -> FakeFont:
            requested.append(size)
            return FakeFont(size)

        surface = fit_text_surface(
            "abcd",
            {"font_size": 20, "font_family": "Arial", "font_weight": "normal", "font_style": "normal"},
            pygame.Rect(0, 0, 60, 20),
            (255, 255, 255),
            font_factory,
        )

        self.assertEqual([20, 19, 18, 17, 16, 15], requested)
        self.assertEqual((60, 15), surface.get_size())

    def test_ellipsized_surface_returns_empty_when_ellipsis_cannot_fit(self) -> None:
        surface = ellipsized_surface(
            "tiny",
            8,
            "default",
            "normal",
            "normal",
            pygame.Rect(0, 0, 4, 4),
            (255, 255, 255),
            lambda size, *_args: FakeFont(size),
        )

        self.assertEqual((0, 0), surface.get_size())


if __name__ == "__main__":
    unittest.main()
