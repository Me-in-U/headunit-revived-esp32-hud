from __future__ import annotations

import unittest

from hud_pi.gauge_geometry import (
    analog_gauge_geometry,
    element_value_ratio,
    gauge_angle_degrees,
    gauge_point,
    gauge_tick_config,
    gauge_tick_entries,
    needle_gauge_geometry,
    sport_gauge_geometry,
    sport_gauge_needle_shape,
    sport_gauge_tick_entries,
    value_ratio,
)


class GaugeGeometryTest(unittest.TestCase):
    def test_value_ratio_clamps_numeric_values_to_element_range(self) -> None:
        self.assertEqual(0.5, value_ratio(110, min_value=0, max_value=220))
        self.assertEqual(0.0, value_ratio(-1, min_value=0, max_value=220))
        self.assertEqual(1.0, value_ratio(250, min_value=0, max_value=220))
        self.assertEqual(0.0, value_ratio(True, min_value=0, max_value=220))
        self.assertEqual(0.25, element_value_ratio("25", {"min_value": 0, "max_value": 100}))

    def test_gauge_angle_maps_ratio_to_needle_sweep(self) -> None:
        self.assertEqual(135.0, gauge_angle_degrees(0.0))
        self.assertEqual(270.0, gauge_angle_degrees(0.5))
        self.assertEqual(405.0, gauge_angle_degrees(1.0))
        self.assertEqual(135.0, gauge_angle_degrees(-1.0))
        self.assertEqual(405.0, gauge_angle_degrees(2.0))

    def test_gauge_point_uses_renderer_coordinate_system(self) -> None:
        self.assertEqual((100, 32), gauge_point((100, 100), radius=80, ratio=0.5, length_ratio=0.85))

    def test_gauge_geometry_helpers_match_renderer_center_and_radius_rules(self) -> None:
        rect = (10, 20, 200, 100)

        self.assertEqual(((110, 82), 66), analog_gauge_geometry(rect))
        self.assertEqual(((110, 108), 78), needle_gauge_geometry(rect))
        self.assertEqual(((110, 86), 62), sport_gauge_geometry(rect))

    def test_gauge_tick_config_preserves_renderer_auto_interval_rules(self) -> None:
        speed_ticks = gauge_tick_config({"min_value": 0, "max_value": 220})
        rpm_ticks = gauge_tick_config({"min_value": 0, "max_value": 8000})

        self.assertEqual(20, speed_ticks.interval)
        self.assertEqual(11, speed_ticks.count)
        self.assertEqual(1000, rpm_ticks.interval)
        self.assertEqual(8, rpm_ticks.count)

    def test_gauge_tick_config_uses_explicit_positive_interval(self) -> None:
        ticks = gauge_tick_config({"min_value": 0, "max_value": 220, "tick_interval": 20})

        self.assertEqual(0.0, ticks.min_value)
        self.assertEqual(220.0, ticks.max_value)
        self.assertEqual(220.0, ticks.range_value)
        self.assertEqual(20.0, ticks.interval)
        self.assertEqual(11, ticks.count)

    def test_gauge_tick_entries_match_renderer_line_and_label_geometry(self) -> None:
        entries = gauge_tick_entries(
            {"min_value": 0, "max_value": 40, "tick_interval": 20},
            center=(100, 100),
            radius=80,
            outer_ratio=1.0,
            major_inner_ratio=0.82,
            minor_inner_ratio=0.90,
            label_ratio=0.70,
        )

        self.assertEqual(3, len(entries))
        self.assertEqual((54, 146), entries[0].inner)
        self.assertEqual((44, 156), entries[0].outer)
        self.assertEqual("0", entries[0].label)
        self.assertEqual((61, 139), entries[0].label_pos)
        self.assertFalse(entries[1].is_major)
        self.assertIsNone(entries[1].label)
        self.assertEqual((100, 28), entries[1].inner)
        self.assertEqual((100, 20), entries[1].outer)
        self.assertEqual("40", entries[2].label)
        self.assertEqual((139, 139), entries[2].label_pos)

    def test_gauge_tick_entries_support_needle_outer_and_inner_ratios(self) -> None:
        entries = gauge_tick_entries(
            {"min_value": 0, "max_value": 40, "tick_interval": 20},
            center=(100, 100),
            radius=80,
            outer_ratio=0.96,
            major_inner_ratio=0.84,
            minor_inner_ratio=0.88,
            label_ratio=0.72,
        )

        self.assertEqual((53, 147), entries[0].inner)
        self.assertEqual((46, 154), entries[0].outer)
        self.assertEqual((60, 140), entries[0].label_pos)

    def test_sport_gauge_tick_entries_match_renderer_tick_geometry(self) -> None:
        entries = sport_gauge_tick_entries(
            {"min_value": 0, "max_value": 4000, "tick_interval": 1000},
            center=(100, 100),
            radius=80,
        )

        self.assertEqual(17, len(entries))
        self.assertEqual((51, 149), entries[0].inner)
        self.assertEqual((44, 156), entries[0].outer)
        self.assertTrue(entries[0].is_major)
        self.assertFalse(entries[0].is_redline)
        self.assertEqual(3, entries[0].line_width)
        self.assertEqual("0", entries[0].label)
        self.assertEqual((60, 140), entries[0].label_pos)

        self.assertFalse(entries[1].is_major)
        self.assertFalse(entries[1].is_redline)
        self.assertEqual(1, entries[1].line_width)
        self.assertIsNone(entries[1].label)
        self.assertIsNone(entries[1].label_pos)

        self.assertFalse(entries[12].is_redline)
        self.assertTrue(entries[13].is_redline)
        self.assertEqual((149, 149), entries[16].inner)
        self.assertEqual((156, 156), entries[16].outer)
        self.assertTrue(entries[16].is_major)
        self.assertTrue(entries[16].is_redline)
        self.assertEqual("4", entries[16].label)
        self.assertEqual((140, 140), entries[16].label_pos)

    def test_sport_gauge_needle_shape_matches_renderer_head_and_tail_geometry(self) -> None:
        self.assertEqual(
            ((47, 153), (111, 89)),
            sport_gauge_needle_shape(center=(100, 100), radius=80, ratio=0.0),
        )
        self.assertEqual(
            ((100, 24), (100, 116)),
            sport_gauge_needle_shape(center=(100, 100), radius=80, ratio=0.5),
        )
        self.assertEqual(
            ((153, 153), (89, 89)),
            sport_gauge_needle_shape(center=(100, 100), radius=80, ratio=1.0),
        )


if __name__ == "__main__":
    unittest.main()
