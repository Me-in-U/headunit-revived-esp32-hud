from __future__ import annotations

import unittest

from hud_pi.gauge_values import (
    element_value_ratio,
    gauge_angle_degrees,
    gauge_point,
    value_ratio,
)


class GaugeValuesTest(unittest.TestCase):
    def test_value_ratio_and_angle_helpers_preserve_gauge_mapping(self) -> None:
        self.assertEqual(0.5, value_ratio(110, min_value=0, max_value=220))
        self.assertEqual(0.0, value_ratio(-1, min_value=0, max_value=220))
        self.assertEqual(1.0, value_ratio(250, min_value=0, max_value=220))
        self.assertEqual(0.0, value_ratio(True, min_value=0, max_value=220))
        self.assertEqual(0.25, element_value_ratio("25", {"min_value": 0, "max_value": 100}))

        self.assertEqual(135.0, gauge_angle_degrees(0.0))
        self.assertEqual(270.0, gauge_angle_degrees(0.5))
        self.assertEqual(405.0, gauge_angle_degrees(1.0))
        self.assertEqual((100, 32), gauge_point((100, 100), radius=80, ratio=0.5, length_ratio=0.85))


if __name__ == "__main__":
    unittest.main()
