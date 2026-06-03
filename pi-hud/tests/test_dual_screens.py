from __future__ import annotations

import unittest
import os
from unittest.mock import patch

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from hud_pi.renderer import HudRenderer
from hud_pi.state import HudState


def text_element(element_id: str, label: str) -> dict:
    return {
        "id": element_id,
        "type": "text",
        "text": label,
        "x": 0,
        "y": 0,
        "w": 200,
        "h": 40,
        "font_size": 20,
        "color": "#ffffff",
        "visible": True,
        "z": 1,
    }


class DualScreenRendererTest(unittest.TestCase):
    def test_renderer_uses_standalone_screen_when_bridge_nav_is_disconnected(self) -> None:
        layout = {
            "canvas": {"width": 1920, "height": 480, "background": "#000000"},
            "screens": {
                "standalone": {"elements": [text_element("standalone_label", "Standalone")]},
                "bridge": {"elements": [text_element("bridge_label", "Bridge")]},
            },
        }
        renderer = HudRenderer(layout, pygame.Surface((1920, 480)))
        drawn: list[str] = []

        with patch.object(renderer, "_draw_textual", side_effect=lambda element, _state: drawn.append(element["id"])):
            renderer.render(HudState({"nav": {"connected": False}}))

        self.assertEqual(["standalone_label"], drawn)

    def test_renderer_uses_bridge_screen_when_bridge_nav_is_connected(self) -> None:
        layout = {
            "canvas": {"width": 1920, "height": 480, "background": "#000000"},
            "screens": {
                "standalone": {"elements": [text_element("standalone_label", "Standalone")]},
                "bridge": {"elements": [text_element("bridge_label", "Bridge")]},
            },
        }
        renderer = HudRenderer(layout, pygame.Surface((1920, 480)))
        drawn: list[str] = []

        with patch.object(renderer, "_draw_textual", side_effect=lambda element, _state: drawn.append(element["id"])):
            renderer.render(HudState({"nav": {"connected": True}}))

        self.assertEqual(["bridge_label"], drawn)

    def test_renderer_starts_fade_transition_when_bridge_screen_changes(self) -> None:
        layout = {
            "canvas": {"width": 1920, "height": 480, "background": "#000000"},
            "screen_transition": {"type": "fade", "duration_ms": 500},
            "screens": {
                "standalone": {"elements": [text_element("standalone_label", "Standalone")]},
                "bridge": {"elements": [text_element("bridge_label", "Bridge")]},
            },
        }
        renderer = HudRenderer(layout, pygame.Surface((1920, 480)))
        drawn: list[str] = []

        with patch("hud_pi.renderer.time.monotonic", side_effect=[1.0, 1.1]), patch.object(
            renderer, "_draw_textual", side_effect=lambda element, _state: drawn.append(element["id"])
        ):
            renderer.render(HudState({"nav": {"connected": False}}))
            renderer.render(HudState({"nav": {"connected": True}}))

        self.assertEqual(["standalone_label", "standalone_label", "bridge_label"], drawn)
        self.assertEqual("bridge", renderer.active_screen_name)
        self.assertEqual("standalone", renderer.previous_screen_name)


if __name__ == "__main__":
    unittest.main()
