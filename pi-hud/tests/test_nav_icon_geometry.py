from __future__ import annotations

import unittest

from hud_pi.nav_icon_geometry import (
    arrow_head_segments,
    corner_arrow_shape,
    lucide_point,
    straight_arrow_segments,
    uturn_shape,
)


class NavIconGeometryTest(unittest.TestCase):
    def test_lucide_point_matches_renderer_coordinate_mapping(self) -> None:
        self.assertEqual((130, 110), lucide_point((10, 20, 240, 120), 12, 19))
        self.assertEqual((64, 79), lucide_point((10, 20, 240, 120), 5, 12))

    def test_straight_arrow_segments_match_renderer_lucide_lines(self) -> None:
        self.assertEqual(
            [
                ((130, 110), (130, 49)),
                ((64, 79), (130, 49)),
                ((195, 79), (130, 49)),
            ],
            straight_arrow_segments((10, 20, 240, 120)),
        )

    def test_corner_arrow_shape_returns_polyline_and_head_segments(self) -> None:
        shape = corner_arrow_shape((0, 0, 240, 120), "left")

        self.assertEqual([(195, 95), (195, 64), (157, 46), (44, 46)], shape.polyline)
        self.assertEqual([((91, 68), (44, 46)), ((91, 24), (44, 46))], shape.head_segments)

    def test_arrow_head_segments_support_right_down_and_left(self) -> None:
        self.assertEqual([((92, 42), (100, 50)), ((92, 58), (100, 50))], arrow_head_segments((100, 50), "right", 4))
        self.assertEqual([((92, 42), (100, 50)), ((108, 42), (100, 50))], arrow_head_segments((100, 50), "down", 4))
        self.assertEqual([((108, 42), (100, 50)), ((108, 58), (100, 50))], arrow_head_segments((100, 50), "left", 4))

    def test_uturn_shape_preserves_renderer_arc_and_arrow_geometry(self) -> None:
        shape = uturn_shape((0, 0, 240, 120), 4)

        self.assertEqual((44, 24, 120, 60), shape.arc_rect)
        self.assertEqual(((176, 95), (176, 59)), shape.line_segment)
        self.assertEqual([((55, 51), (63, 59)), ((71, 51), (63, 59))], shape.head_segments)


if __name__ == "__main__":
    unittest.main()
