from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from hud_pi.pygame_layer import render_alpha_layer


class FakeTarget:
    def __init__(self) -> None:
        self.blits: list[tuple[FakeLayer, tuple[int, int]]] = []

    def get_width(self) -> int:
        return 100

    def get_height(self) -> int:
        return 50

    def blit(self, layer: "FakeLayer", position: tuple[int, int]) -> None:
        self.blits.append((layer, position))


class FakeLayer:
    def __init__(self) -> None:
        self.alpha: int | None = None

    def set_alpha(self, alpha: int) -> None:
        self.alpha = alpha


class PygameLayerTest(unittest.TestCase):
    def test_render_alpha_layer_creates_layer_clamps_alpha_and_blits(self) -> None:
        target = FakeTarget()
        layer = FakeLayer()
        rendered_layers: list[FakeLayer] = []

        with patch("hud_pi.pygame_layer.pygame.Surface", return_value=layer) as surface:
            render_alpha_layer(
                target,  # type: ignore[arg-type]
                300,
                lambda render_layer: rendered_layers.append(render_layer),  # type: ignore[arg-type]
            )

        surface.assert_called_once_with((100, 50), pygame.SRCALPHA)
        self.assertEqual([layer], rendered_layers)
        self.assertEqual(255, layer.alpha)
        self.assertEqual([(layer, (0, 0))], target.blits)


if __name__ == "__main__":
    unittest.main()
