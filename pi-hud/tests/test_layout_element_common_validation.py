from __future__ import annotations

import unittest

from hud_pi.layout_element_common_validation import (
    validate_binding_shapes,
    validate_element_bounds,
    validate_element_colors,
)


class LayoutElementCommonValidationTest(unittest.TestCase):
    def test_common_element_validation_preserves_geometry_color_and_binding_errors(self) -> None:
        element = {
            "binding": 42,
            "fallback_bindings": "vehicle.speed_kmh_backup",
            "bindings": ["vehicle.speed_kmh", 7],
            "x": -1,
            "y": 0,
            "w": 300,
            "h": 20,
            "font_size": 7,
            "color": "white",
        }

        errors = [
            *validate_element_bounds(element, "speed", canvas_width=200, canvas_height=100),
            *validate_element_colors(element, "speed"),
            *validate_binding_shapes(element, "speed"),
        ]

        self.assertIn("element 'speed' x and y must be non-negative", errors)
        self.assertIn("element 'speed' exceeds canvas width", errors)
        self.assertIn("element 'speed' font_size must be at least 8", errors)
        self.assertIn("element 'speed' color 'white' must be #RGB or #RRGGBB", errors)
        self.assertIn("element 'speed' binding must be a string", errors)
        self.assertIn("element 'speed' fallback_bindings must be a list of strings", errors)
        self.assertIn("element 'speed' bindings[1] must be a string", errors)


if __name__ == "__main__":
    unittest.main()
