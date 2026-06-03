from __future__ import annotations

import unittest

from hud_pi.gear_indicator import (
    DEFAULT_GEARS,
    active_only_display,
    gear_indicator_entries,
    normalize_active_gear,
    normalize_gears,
)


class GearIndicatorTest(unittest.TestCase):
    def test_normalize_gears_accepts_list_values_and_falls_back_when_empty(self) -> None:
        self.assertEqual(("P", "R", "N", "D", "3", "2", "L"), DEFAULT_GEARS)
        self.assertEqual(("P", "R", "N", "D"), normalize_gears([" p ", "r", "N", " d "]))
        self.assertEqual(DEFAULT_GEARS, normalize_gears([" ", ""]))
        self.assertEqual(DEFAULT_GEARS, normalize_gears("P,R,N,D"))

    def test_normalize_active_gear_and_active_only_display(self) -> None:
        self.assertEqual("D", normalize_active_gear(" d "))
        self.assertEqual("--", normalize_active_gear(None))
        self.assertEqual("--", active_only_display(""))
        self.assertEqual("--", active_only_display("--"))
        self.assertEqual("R", active_only_display("R"))

    def test_gear_indicator_entries_compute_strip_slots_and_active_style(self) -> None:
        entries = gear_indicator_entries(
            {
                "gears": ["P", "R", "N", "D"],
                "font_size": 20,
                "active_font_size": 44,
                "font_family": "Verdana",
                "font_weight": "normal",
                "font_style": "italic",
                "color": "#ffffff",
                "active_color": "#00ff00",
            },
            "d",
            rect=(10, 20, 100, 30),
        )

        self.assertEqual(["P", "R", "N", "D"], [entry.label for entry in entries])
        self.assertEqual([(10, 20, 25, 30), (35, 20, 25, 30), (60, 20, 25, 30), (85, 20, 25, 30)], [entry.rect for entry in entries])
        self.assertEqual([20, 20, 20, 44], [entry.font_size for entry in entries])
        self.assertEqual(["normal", "normal", "normal", "bold"], [entry.font_weight for entry in entries])
        self.assertEqual((0, 255, 0), entries[-1].color)
        self.assertEqual("Verdana", entries[-1].font_family)
        self.assertEqual("italic", entries[-1].font_style)

    def test_gear_indicator_entries_compute_active_only_display(self) -> None:
        active = gear_indicator_entries(
            {
                "gear_style": "active_only",
                "font_size": 20,
                "active_font_size": 44,
                "active_color": "#00ff00",
                "inactive_color": "#333333",
            },
            "D",
            rect=(10, 20, 100, 30),
        )
        missing = gear_indicator_entries(
            {
                "gear_style": "active_only",
                "font_size": 20,
                "active_font_size": 44,
                "active_color": "#00ff00",
                "inactive_color": "#333333",
            },
            None,
            rect=(10, 20, 100, 30),
        )

        self.assertEqual(1, len(active))
        self.assertEqual("D", active[0].label)
        self.assertEqual((10, 20, 100, 30), active[0].rect)
        self.assertEqual((0, 255, 0), active[0].color)
        self.assertEqual("--", missing[0].label)
        self.assertEqual((51, 51, 51), missing[0].color)


if __name__ == "__main__":
    unittest.main()
