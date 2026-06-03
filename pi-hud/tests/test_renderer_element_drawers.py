from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from hud_pi.renderer_element_drawers import RendererElementDrawersMixin
from hud_pi.state import HudState


class DrawerRenderer(RendererElementDrawersMixin):
    def __init__(self) -> None:
        self.screen = pygame.Surface((100, 100))
        self.canvas = {"width": 100, "height": 100}
        self.language = "ko"

    def _rect(self, element):
        return pygame.Rect(element.get("x", 0), element.get("y", 0), element.get("w", 0), element.get("h", 0))

    def _rect_tuple(self, rect):
        return (rect.x, rect.y, rect.w, rect.h)

    def _load_nav_icon(self, _name):
        return pygame.Surface((10, 10), pygame.SRCALPHA)


class RendererElementDrawersTest(unittest.TestCase):
    def test_nav_icon_drawer_skips_invalid_rect_and_calls_nav_renderer_for_valid_rect(self) -> None:
        renderer = DrawerRenderer()
        state = HudState({"nav": {"event_type": 4}})

        with patch("hud_pi.renderer_element_drawers.draw_nav_icon_element") as draw_nav_icon:
            renderer._draw_nav_icon({"id": "bad", "type": "nav_icon", "w": 0, "h": 40}, state)
            renderer._draw_nav_icon({"id": "nav", "type": "nav_icon", "x": 1, "y": 2, "w": 30, "h": 40}, state)

        draw_nav_icon.assert_called_once()
        self.assertEqual((1, 2, 30, 40), draw_nav_icon.call_args.kwargs["rect"])
        self.assertEqual(state.resolve, draw_nav_icon.call_args.kwargs["resolve"])


if __name__ == "__main__":
    unittest.main()
