from __future__ import annotations

import unittest

from hud_pi.layout_vehicle_validation import validate_vehicles


class LayoutVehicleValidationTest(unittest.TestCase):
    def test_vehicle_validation_preserves_profile_id_and_label_errors(self) -> None:
        errors, vehicle_ids = validate_vehicles(
            [
                {"id": "car_a", "label": "Car A"},
                {"id": "car_a", "label": "Duplicate"},
                {"id": "", "label": ""},
                "bad",
            ]
        )

        self.assertEqual({"car_a"}, vehicle_ids)
        self.assertEqual(
            [
                "duplicate vehicle id 'car_a'",
                "vehicle at index 2 is missing id",
                "vehicle at index 2 is missing label",
                "vehicle at index 3 must be an object",
            ],
            errors,
        )


if __name__ == "__main__":
    unittest.main()
