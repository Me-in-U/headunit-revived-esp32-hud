from __future__ import annotations

import unittest

from hud_pi.layout_value_validation import validate_value_config


class LayoutValueValidationTest(unittest.TestCase):
    def test_value_config_validation_preserves_style_and_range_errors(self) -> None:
        errors = validate_value_config(
            {
                "type": "value",
                "value_style": "sparkline",
                "min_value": 20,
                "max_value": 10,
            },
            "speed",
        )

        self.assertIn("element 'speed' value_style 'sparkline' is not supported", errors)
        self.assertIn("element 'speed' max_value must be greater than min_value", errors)

    def test_value_config_validation_ignores_non_value_elements(self) -> None:
        self.assertEqual([], validate_value_config({"type": "text", "value_style": "sparkline"}, "label"))


if __name__ == "__main__":
    unittest.main()
