from __future__ import annotations

import unittest

from hud_pi.layout_gear_validation import validate_gear_config


class LayoutGearValidationTest(unittest.TestCase):
    def test_gear_config_validation_preserves_style_gears_and_active_font_errors(self) -> None:
        errors = validate_gear_config(
            {
                "type": "gear_indicator",
                "gear_style": "rpm",
                "gears": ["P", ""],
                "active_font_size": 4,
            },
            "gear",
        )

        self.assertIn("element 'gear' gear_style 'rpm' is not supported", errors)
        self.assertIn("element 'gear' gears[1] must be a non-empty string", errors)
        self.assertIn("element 'gear' active_font_size must be at least 8", errors)

    def test_gear_config_validation_ignores_non_gear_elements(self) -> None:
        self.assertEqual([], validate_gear_config({"type": "value", "gear_style": "rpm"}, "speed"))


if __name__ == "__main__":
    unittest.main()
