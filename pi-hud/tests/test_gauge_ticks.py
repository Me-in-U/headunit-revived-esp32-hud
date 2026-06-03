from __future__ import annotations

import unittest

from hud_pi.gauge_ticks import gauge_tick_config, gauge_tick_entries, sport_gauge_tick_entries


class GaugeTicksTest(unittest.TestCase):
    def test_tick_config_and_entries_preserve_renderer_tick_geometry(self) -> None:
        speed_ticks = gauge_tick_config({"min_value": 0, "max_value": 220})
        self.assertEqual(20, speed_ticks.interval)
        self.assertEqual(11, speed_ticks.count)

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
        self.assertFalse(entries[1].is_major)
        self.assertEqual("40", entries[2].label)

    def test_sport_tick_entries_preserve_redline_and_label_rules(self) -> None:
        entries = sport_gauge_tick_entries(
            {"min_value": 0, "max_value": 4000, "tick_interval": 1000},
            center=(100, 100),
            radius=80,
        )

        self.assertEqual(17, len(entries))
        self.assertTrue(entries[0].is_major)
        self.assertFalse(entries[0].is_redline)
        self.assertFalse(entries[12].is_redline)
        self.assertTrue(entries[13].is_redline)
        self.assertEqual("4", entries[16].label)


if __name__ == "__main__":
    unittest.main()
