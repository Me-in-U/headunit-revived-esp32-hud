from __future__ import annotations

import unittest

from hud_pi.layout_bindings import element_bindings, has_path


class LayoutBindingsTest(unittest.TestCase):
    def test_element_bindings_collects_primary_fallback_row_and_nav_bindings(self) -> None:
        element = {
            "binding": " vehicle.speed_kmh ",
            "fallback_bindings": ["vehicle.backup_speed", "", 42],
            "bindings": ["warnings.abs", None, " warnings.brake "],
            "event_binding": "nav.event",
            "side_binding": "nav.side",
        }

        self.assertEqual(
            [
                "vehicle.speed_kmh",
                "vehicle.backup_speed",
                "warnings.abs",
                "warnings.brake",
                "nav.event",
                "nav.side",
            ],
            element_bindings(element),
        )

    def test_has_path_checks_nested_dummy_data_paths(self) -> None:
        dummy_data = {"vehicle": {"speed_kmh": 42}, "warnings": {"abs": False}}

        self.assertTrue(has_path(dummy_data, "vehicle.speed_kmh"))
        self.assertFalse(has_path(dummy_data, "vehicle.rpm"))
        self.assertFalse(has_path(dummy_data, "vehicle.speed_kmh.value"))


if __name__ == "__main__":
    unittest.main()
