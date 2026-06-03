from __future__ import annotations

import copy
import unittest

from hud_pi.layout import load_layout
from hud_pi.layout_validation import validate_layout


class LayoutValidationModuleTest(unittest.TestCase):
    def test_validation_module_rejects_bad_value_and_gear_styles(self) -> None:
        layout = load_layout("layouts/avante_hd_2010_default.json")
        invalid = copy.deepcopy(layout)
        speed = next(element for element in invalid["elements"] if element.get("id") == "speed")
        gear = next(element for element in invalid["elements"] if element.get("id") == "gear_range")
        speed["value_style"] = "sparkline"
        gear["gear_style"] = "rpm"

        errors = validate_layout(invalid)

        self.assertIn("element 'speed' value_style 'sparkline' is not supported", errors)
        self.assertIn("element 'gear_range' gear_style 'rpm' is not supported", errors)


if __name__ == "__main__":
    unittest.main()
