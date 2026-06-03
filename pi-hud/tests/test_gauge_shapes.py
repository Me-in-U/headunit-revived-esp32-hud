from __future__ import annotations

import unittest

from hud_pi.gauge_shapes import (
    analog_gauge_geometry,
    needle_gauge_geometry,
    sport_gauge_geometry,
    sport_gauge_needle_shape,
)


class GaugeShapesTest(unittest.TestCase):
    def test_geometry_and_needle_shape_preserve_renderer_rules(self) -> None:
        rect = (10, 20, 200, 100)

        self.assertEqual(((110, 82), 66), analog_gauge_geometry(rect))
        self.assertEqual(((110, 108), 78), needle_gauge_geometry(rect))
        self.assertEqual(((110, 86), 62), sport_gauge_geometry(rect))
        self.assertEqual(
            ((100, 24), (100, 116)),
            sport_gauge_needle_shape(center=(100, 100), radius=80, ratio=0.5),
        )


if __name__ == "__main__":
    unittest.main()
