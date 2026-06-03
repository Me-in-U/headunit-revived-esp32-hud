from __future__ import annotations

import unittest

from hud_pi.renderer_element_dispatch import RendererElementDispatchMixin
from hud_pi.state import HudState


class DispatchRenderer(RendererElementDispatchMixin):
    def __init__(self) -> None:
        self.drawn: list[str] = []

    def _draw_warning_row(self, element, _state):
        self.drawn.append(f"warning_row:{element['id']}")

    def _draw_warning_icon(self, element, _state):
        self.drawn.append(f"warning_icon:{element['id']}")

    def _draw_nav_icon(self, element, _state):
        self.drawn.append(f"nav_icon:{element['id']}")

    def _draw_gear_indicator(self, element, _state):
        self.drawn.append(f"gear_indicator:{element['id']}")

    def _draw_textual(self, element, _state):
        self.drawn.append(f"text:{element['id']}")


class RendererElementDispatchTest(unittest.TestCase):
    def test_dispatch_mixin_preserves_visible_sorted_render_action_order(self) -> None:
        renderer = DispatchRenderer()
        elements = [
            {"id": "hidden", "type": "text", "visible": False, "z": 0},
            {"id": "text", "type": "text", "z": 1},
            {"id": "warning", "type": "warning_icon", "z": 2},
            {"id": "nav", "type": "nav_icon", "z": 3},
            {"id": "gear", "type": "gear_indicator", "z": 4},
            {"id": "row", "type": "warning_row", "z": 5},
        ]

        renderer._render_elements(elements, HudState({}))

        self.assertEqual(
            [
                "text:text",
                "warning_icon:warning",
                "nav_icon:nav",
                "gear_indicator:gear",
                "warning_row:row",
            ],
            renderer.drawn,
        )


if __name__ == "__main__":
    unittest.main()
