from __future__ import annotations

import os
import unittest

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from hud_pi.renderer_support import RendererSupportMixin
from hud_pi.viewport_scale import ViewportScale


class SupportRenderer(RendererSupportMixin):
    def __init__(self) -> None:
        self.viewport_scale = ViewportScale(2.0, 3.0)


class RendererSupportTest(unittest.TestCase):
    def test_renderer_support_preserves_rect_scale_and_tuple_helpers(self) -> None:
        renderer = SupportRenderer()
        element = {"x": 10, "y": 20, "w": 30, "h": 40}

        rect = renderer._rect(element)

        self.assertEqual((20, 60, 60, 120), (rect.x, rect.y, rect.width, rect.height))
        self.assertEqual((20, 60, 60, 120), renderer._rect_tuple(rect))
        self.assertEqual(20, renderer._x(10))
        self.assertEqual(60, renderer._y(20))
        self.assertEqual(60, renderer._s(30))

    def test_renderer_support_loads_background_image_through_cache_slot(self) -> None:
        renderer = SupportRenderer()
        renderer.canvas = {"background_image": None}
        cached = ("old", pygame.Surface((1, 1)))
        renderer.background_image_cache = cached

        self.assertIsNone(renderer._load_background_image())
        self.assertIs(cached, renderer.background_image_cache)


if __name__ == "__main__":
    unittest.main()
