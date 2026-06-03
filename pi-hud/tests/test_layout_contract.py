from __future__ import annotations

import unittest

from hud_pi.layout import load_layout


EXPECTED_DLC_PINS = [16, 15, 14, 12, 8, 6, 5, 4, 3]
EXPECTED_WARNING_LAMPS = [
    "door_open",
    "battery",
    "brake",
    "abs",
    "airbag",
    "oil_pressure",
    "check_engine",
    "eps",
    "coolant_temp",
]


def has_path(root: dict, path: str) -> bool:
    node = root
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return False
        node = node[part]
    return True


def null_paths(root: dict, prefix: str = "") -> list[str]:
    paths: list[str] = []
    for key, value in root.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        if value is None:
            paths.append(path)
        elif isinstance(value, dict):
            paths.extend(null_paths(value, path))
    return paths


def all_elements(layout: dict) -> list[dict]:
    elements = list(layout.get("elements", []))
    for screen in layout.get("screens", {}).values():
        if isinstance(screen, dict):
            elements.extend(screen.get("elements", []))
    return elements


class LayoutContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.layout = load_layout("layouts/avante_hd_2010_default.json")

    def test_default_layout_is_1920_by_480(self) -> None:
        self.assertEqual(1920, self.layout["canvas"]["width"])
        self.assertEqual(480, self.layout["canvas"]["height"])

    def test_default_vehicle_contains_confirmed_avante_hd_values(self) -> None:
        self.assertEqual("avante_hd_2010_1_6_at", self.layout["selected_vehicle"])
        vehicle = self.layout["vehicles"][0]
        confirmed = vehicle["confirmed"]

        self.assertEqual("2010 아반떼 HD 1.6 가솔린 자동", vehicle["description_ko"])
        self.assertTrue(confirmed["abs"])
        self.assertIsNone(confirmed["esc_tcs"])
        self.assertFalse(confirmed["tpms"])
        self.assertEqual("P/R/N/D/3/2/L", confirmed["gear_range_display"])
        self.assertEqual(EXPECTED_DLC_PINS, confirmed["dlc_pins"])
        self.assertEqual(EXPECTED_WARNING_LAMPS, confirmed["warning_lamps"])

    def test_all_element_bindings_have_dummy_values(self) -> None:
        dummy_data = self.layout["dummy_data"]
        missing: list[str] = []
        for element in self.layout["elements"]:
            for binding in [element.get("binding", "")] + list(element.get("fallback_bindings", [])):
                if binding and not has_path(dummy_data, binding):
                    missing.append(f"{element['id']}:{binding}")
            for binding in element.get("bindings", []):
                if binding and not has_path(dummy_data, binding):
                    missing.append(f"{element['id']}:{binding}")

        self.assertEqual([], missing)

    def test_default_dummy_data_has_no_null_placeholders(self) -> None:
        self.assertEqual([], null_paths(self.layout["dummy_data"]))

    def test_speed_element_keeps_android_speed_as_backup_only(self) -> None:
        speed = next(element for element in self.layout["elements"] if element["id"] == "speed")

        self.assertEqual("vehicle.speed_kmh", speed["binding"])
        self.assertEqual(["vehicle.speed_kmh_backup"], speed["fallback_bindings"])

    def test_default_layout_has_pi_local_can_diagnostics(self) -> None:
        self.assertTrue(has_path(self.layout["dummy_data"], "vehicle.can_state"))
        self.assertTrue(has_path(self.layout["dummy_data"], "debug.can_frame_count"))
        self.assertTrue(has_path(self.layout["dummy_data"], "debug.last_can_id"))

        can_state = next(element for element in self.layout["elements"] if element["id"] == "can_state")
        self.assertEqual("diagnostics", can_state["category"])
        self.assertEqual("vehicle.can_state", can_state["binding"])

    def test_default_layout_has_standalone_and_bridge_screens_with_fade_transition(self) -> None:
        screens = self.layout.get("screens", {})
        transition = self.layout.get("screen_transition", {})

        self.assertEqual("fade", transition.get("type"))
        self.assertGreaterEqual(transition.get("duration_ms", 0), 250)
        self.assertIn("standalone", screens)
        self.assertIn("bridge", screens)
        self.assertGreater(len(screens["standalone"]["elements"]), 0)
        self.assertGreater(len(screens["bridge"]["elements"]), 0)
        self.assertTrue(any(element["id"].startswith("warning_") for element in screens["standalone"]["elements"]))
        self.assertTrue(any(element["id"].startswith("nav_") for element in screens["bridge"]["elements"]))

    def test_default_layout_does_not_use_car_scene(self) -> None:
        self.assertNotIn("car_scene", {element.get("type") for element in all_elements(self.layout)})

    def test_default_rpm_element_uses_sport_gauge_with_max_value(self) -> None:
        rpm = next(element for element in self.layout["elements"] if element["id"] == "rpm")

        self.assertEqual("sport_gauge", rpm["value_style"])
        self.assertEqual(8000, rpm["max_value"])
        self.assertFalse(rpm.get("show_value_label", False))

    def test_default_layout_splits_graphics_and_numeric_values(self) -> None:
        elements = {element["id"]: element for element in self.layout["elements"]}

        self.assertEqual("sport_gauge", elements["rpm"]["value_style"])
        self.assertEqual("vehicle.rpm", elements["rpm_value"]["binding"])
        self.assertEqual("digital", elements["rpm_value"]["value_style"])
        self.assertEqual("bar", elements["fuel"]["value_style"])
        self.assertEqual("vehicle.fuel_percent", elements["fuel_value"]["binding"])
        self.assertEqual("digital", elements["fuel_value"]["value_style"])

    def test_default_layout_has_weather_dummy_data_and_temperature_element(self) -> None:
        self.assertTrue(has_path(self.layout["dummy_data"], "weather.temp_c"))
        self.assertTrue(has_path(self.layout["dummy_data"], "weather.condition_ko"))

        weather = next(element for element in self.layout["elements"] if element["id"] == "weather_temp")
        self.assertEqual("weather.temp_c", weather["binding"])

    def test_default_navigation_instruction_does_not_duplicate_distance(self) -> None:
        dummy_nav = self.layout["dummy_data"]["nav"]
        instruction = str(dummy_nav["instruction"])

        self.assertEqual("우회전", instruction)
        self.assertEqual(300, dummy_nav["distance_meters"])
        self.assertNotIn("300", instruction)
        self.assertNotIn("m", instruction.lower())

    def test_default_layout_has_numeric_navigation_icon_element(self) -> None:
        elements = all_elements(self.layout)
        icons = [element for element in elements if element.get("type") == "nav_icon"]

        self.assertTrue(icons)
        self.assertTrue(any(element.get("event_binding") == "nav.event_type" for element in icons))
        self.assertTrue(any(element.get("side_binding") == "nav.turn_side" for element in icons))

    def test_default_gear_uses_dedicated_indicator_not_value_style(self) -> None:
        gears = [element for element in all_elements(self.layout) if element.get("id") == "gear_range"]

        self.assertTrue(gears)
        for gear in gears:
            self.assertEqual("gear_indicator", gear.get("type"))
            self.assertNotIn("value_style", gear)
            self.assertEqual(["P", "R", "N", "D", "3", "2", "L"], gear.get("gears"))
            self.assertIn(gear.get("gear_style"), {"strip", "active_only"})


if __name__ == "__main__":
    unittest.main()
