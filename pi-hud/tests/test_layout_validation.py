from __future__ import annotations

import copy
import unittest

from hud_pi.layout import load_layout, normalize_layout_for_save, validate_layout


class LayoutValidationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.layout = load_layout("layouts/avante_hd_2010_default.json")

    def test_default_layout_has_no_validation_errors(self) -> None:
        self.assertEqual([], validate_layout(self.layout))

    def test_validate_layout_rejects_unknown_selected_vehicle(self) -> None:
        layout = copy.deepcopy(self.layout)
        layout["selected_vehicle"] = "missing_vehicle"

        self.assertIn("selected_vehicle 'missing_vehicle' is not present in vehicles", validate_layout(layout))

    def test_validate_layout_rejects_invalid_vehicle_profile_entries(self) -> None:
        layout = copy.deepcopy(self.layout)
        layout["vehicles"] = [
            {"id": "avante_hd_2010_1_6_at", "label": "Avante"},
            {"id": "avante_hd_2010_1_6_at", "label": "Duplicate Avante"},
            {"id": "missing_label"},
            {"label": "Missing ID"},
            "not-an-object",
        ]

        errors = validate_layout(layout)

        self.assertIn("duplicate vehicle id 'avante_hd_2010_1_6_at'", errors)
        self.assertIn("vehicle at index 2 is missing label", errors)
        self.assertIn("vehicle at index 3 is missing id", errors)
        self.assertIn("vehicle at index 4 must be an object", errors)

    def test_validate_layout_rejects_duplicate_element_ids(self) -> None:
        layout = copy.deepcopy(self.layout)
        duplicate = copy.deepcopy(layout["elements"][0])
        layout["elements"].append(duplicate)

        self.assertIn("duplicate element id 'gear_range'", validate_layout(layout))

    def test_normalize_layout_for_save_clamps_elements_inside_canvas(self) -> None:
        layout = copy.deepcopy(self.layout)
        element = layout["elements"][0]
        element["x"] = -50
        element["y"] = 9999
        element["w"] = 3000
        element["h"] = 0
        element["font_size"] = -10

        normalized = normalize_layout_for_save(layout)
        normalized_element = normalized["elements"][0]

        self.assertEqual(0, normalized_element["x"])
        self.assertEqual(479, normalized_element["y"])
        self.assertEqual(1920, normalized_element["w"])
        self.assertEqual(1, normalized_element["h"])
        self.assertEqual(8, normalized_element["font_size"])
        self.assertEqual([], validate_layout(normalized))

    def test_normalize_layout_for_save_adds_font_and_alignment_defaults(self) -> None:
        layout = copy.deepcopy(self.layout)
        element = layout["elements"][0]
        element.pop("font_family", None)
        element.pop("font_weight", None)
        element.pop("font_style", None)
        element.pop("align", None)
        element.pop("value_style", None)

        normalized = normalize_layout_for_save(layout)
        normalized_element = normalized["elements"][0]

        self.assertEqual("default", normalized_element["font_family"])
        self.assertEqual("normal", normalized_element["font_weight"])
        self.assertEqual("normal", normalized_element["font_style"])
        self.assertEqual("left", normalized_element["align"])
        if normalized_element["type"] == "value":
            self.assertEqual("digital", normalized_element["value_style"])
        else:
            self.assertNotIn("value_style", normalized_element)

    def test_validate_layout_rejects_missing_dummy_binding(self) -> None:
        layout = copy.deepcopy(self.layout)
        layout["elements"][0]["binding"] = "vehicle.not_in_dummy"

        self.assertIn("element 'gear_range' binding 'vehicle.not_in_dummy' has no dummy_data value", validate_layout(layout))

    def test_validate_layout_rejects_unsupported_element_type(self) -> None:
        layout = copy.deepcopy(self.layout)
        layout["elements"][0]["type"] = "sparkline"

        self.assertIn(
            "element 'gear_range' type 'sparkline' is not supported",
            validate_layout(layout),
        )

    def test_validate_layout_rejects_removed_car_scene_type(self) -> None:
        layout = copy.deepcopy(self.layout)
        layout["elements"][0]["type"] = "car_scene"

        self.assertIn(
            "element 'gear_range' type 'car_scene' is not supported",
            validate_layout(layout),
        )

    def test_validate_layout_checks_screen_specific_elements(self) -> None:
        layout = copy.deepcopy(self.layout)
        layout["screens"]["bridge"]["elements"][0]["binding"] = "vehicle.missing_bridge_value"

        self.assertIn(
            "element 'gear_range' binding 'vehicle.missing_bridge_value' has no dummy_data value",
            validate_layout(layout),
        )

    def test_validate_layout_rejects_non_list_binding_collections(self) -> None:
        layout = copy.deepcopy(self.layout)
        layout["elements"][0]["fallback_bindings"] = "vehicle.speed_kmh_backup"
        speed = next(element for element in layout["elements"] if element.get("id") == "speed")
        speed["bindings"] = "warnings.abs"

        errors = validate_layout(layout)

        self.assertIn("element 'gear_range' fallback_bindings must be a list of strings", errors)
        self.assertIn("element 'speed' bindings must be a list of strings", errors)

    def test_validate_layout_rejects_non_string_binding_entries(self) -> None:
        layout = copy.deepcopy(self.layout)
        layout["elements"][0]["fallback_bindings"] = ["vehicle.speed_kmh_backup", 42]
        speed = next(element for element in layout["elements"] if element.get("id") == "speed")
        speed["bindings"] = ["warnings.abs", None]

        errors = validate_layout(layout)

        self.assertIn("element 'gear_range' fallback_bindings[1] must be a string", errors)
        self.assertIn("element 'speed' bindings[1] must be a string", errors)

    def test_validate_layout_rejects_invalid_canvas_and_element_colors(self) -> None:
        layout = copy.deepcopy(self.layout)
        layout["canvas"]["background"] = "not-a-color"
        layout["elements"][0]["color"] = "#12xx56"
        speed = next(element for element in layout["elements"] if element.get("id") == "speed")
        nav_icon = next(element for element in layout["elements"] if element.get("id") == "nav_icon")
        speed["inactive_color"] = "orange"
        nav_icon["accent"] = "#12345"

        errors = validate_layout(layout)

        self.assertIn("canvas background color 'not-a-color' must be #RGB or #RRGGBB", errors)
        self.assertIn("element 'gear_range' color '#12xx56' must be #RGB or #RRGGBB", errors)
        self.assertIn("element 'speed' inactive_color 'orange' must be #RGB or #RRGGBB", errors)
        self.assertIn("element 'nav_icon' accent '#12345' must be #RGB or #RRGGBB", errors)

    def test_validate_layout_rejects_invalid_value_style_and_range(self) -> None:
        layout = copy.deepcopy(self.layout)
        speed = next(element for element in layout["elements"] if element.get("id") == "speed")
        speed["value_style"] = "sparkline"
        speed["min_value"] = 100
        speed["max_value"] = 50
        rpm = next(element for element in layout["elements"] if element.get("id") == "rpm")
        rpm["max_value"] = "fast"

        errors = validate_layout(layout)

        self.assertIn("element 'speed' value_style 'sparkline' is not supported", errors)
        self.assertIn("element 'speed' max_value must be greater than min_value", errors)
        self.assertIn("element 'rpm' max_value must be numeric", errors)

    def test_validate_layout_rejects_invalid_gear_indicator_config(self) -> None:
        layout = copy.deepcopy(self.layout)
        gear = next(element for element in layout["elements"] if element.get("id") == "gear_range")
        gear["type"] = "gear_indicator"
        gear["gear_style"] = "rpm"
        gear["gears"] = "PRND32L"

        errors = validate_layout(layout)

        self.assertIn("element 'gear_range' gear_style 'rpm' is not supported", errors)
        self.assertIn("element 'gear_range' gears must be a list of strings", errors)


if __name__ == "__main__":
    unittest.main()
