from __future__ import annotations

import unittest

from hud_pi.layout_element_validation import validate_element_list


class LayoutElementValidationTest(unittest.TestCase):
    def test_element_validation_preserves_binding_style_and_geometry_errors(self) -> None:
        errors = validate_element_list(
            [
                {
                    "id": "speed",
                    "type": "value",
                    "binding": "vehicle.speed_kmh",
                    "fallback_bindings": [42],
                    "x": -1,
                    "y": 0,
                    "w": 300,
                    "h": 20,
                    "font_size": 7,
                    "color": "white",
                    "value_style": "sparkline",
                    "min_value": "low",
                    "max_value": 10,
                },
                {
                    "id": "gear",
                    "type": "gear_indicator",
                    "binding": "vehicle.gear",
                    "x": 0,
                    "y": 0,
                    "w": 100,
                    "h": 40,
                    "font_size": 18,
                    "gear_style": "rpm",
                    "gears": ["P", ""],
                    "active_font_size": 4,
                },
            ],
            {"vehicle": {"gear": "D"}},
            200,
            100,
        )

        self.assertIn("element 'speed' x and y must be non-negative", errors)
        self.assertIn("element 'speed' exceeds canvas width", errors)
        self.assertIn("element 'speed' font_size must be at least 8", errors)
        self.assertIn("element 'speed' color 'white' must be #RGB or #RRGGBB", errors)
        self.assertIn("element 'speed' fallback_bindings[0] must be a string", errors)
        self.assertIn("element 'speed' value_style 'sparkline' is not supported", errors)
        self.assertIn("element 'speed' min_value must be numeric", errors)
        self.assertIn("element 'speed' binding 'vehicle.speed_kmh' has no dummy_data value", errors)
        self.assertIn("element 'gear' gear_style 'rpm' is not supported", errors)
        self.assertIn("element 'gear' gears[1] must be a non-empty string", errors)
        self.assertIn("element 'gear' active_font_size must be at least 8", errors)


if __name__ == "__main__":
    unittest.main()
