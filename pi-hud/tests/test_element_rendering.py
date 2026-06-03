from __future__ import annotations

import unittest

from hud_pi.element_rendering import alpha_value, render_action, sorted_visible_elements


class ElementRenderingTest(unittest.TestCase):
    def test_sorted_visible_elements_omits_hidden_and_orders_by_z(self) -> None:
        low = {"id": "low", "z": -1}
        default = {"id": "default"}
        high = {"id": "high", "z": 10}
        hidden = {"id": "hidden", "visible": False, "z": -99}

        self.assertEqual([low, default, high], sorted_visible_elements([high, hidden, default, low]))

    def test_render_action_maps_known_types_and_defaults_to_textual(self) -> None:
        self.assertEqual("warning_row", render_action({"type": "warning_row"}))
        self.assertEqual("warning_icon", render_action({"type": "warning_icon"}))
        self.assertEqual("nav_icon", render_action({"type": "nav_icon"}))
        self.assertEqual("gear_indicator", render_action({"type": "gear_indicator"}))
        self.assertEqual("textual", render_action({"type": "text"}))
        self.assertEqual("textual", render_action({"type": "unknown"}))
        self.assertEqual("textual", render_action({}))

    def test_alpha_value_clamps_layer_alpha_to_pygame_range(self) -> None:
        self.assertEqual(0, alpha_value(-20))
        self.assertEqual(128, alpha_value(128))
        self.assertEqual(255, alpha_value(999))


if __name__ == "__main__":
    unittest.main()
