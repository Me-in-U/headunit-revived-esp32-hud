from __future__ import annotations

import unittest

from hud_pi.value_bar_geometry import value_bar_geometry, value_bar_highlight_color


class ValueBarGeometryTest(unittest.TestCase):
    def test_value_bar_geometry_matches_renderer_rect_and_segment_rules(self) -> None:
        geometry = value_bar_geometry((20, 20, 300, 60), ratio=0.5, min_bar_height=10)

        self.assertEqual((20, 40, 300, 20), geometry.bar_rect)
        self.assertEqual((20, 40, 150, 20), geometry.fill_rect)
        self.assertEqual((20, 40, 150, 6), geometry.highlight_rect)
        self.assertEqual(10, geometry.border_radius)
        self.assertEqual(
            [
                ((50, 40), (50, 60)),
                ((80, 40), (80, 60)),
                ((110, 40), (110, 60)),
                ((140, 40), (140, 60)),
                ((170, 40), (170, 60)),
                ((200, 40), (200, 60)),
                ((230, 40), (230, 60)),
                ((260, 40), (260, 60)),
                ((290, 40), (290, 60)),
            ],
            geometry.segment_lines,
        )

    def test_value_bar_geometry_uses_min_height_and_min_fill_width(self) -> None:
        geometry = value_bar_geometry((0, 0, 120, 12), ratio=0.01, min_bar_height=10)

        self.assertEqual((0, 1, 120, 10), geometry.bar_rect)
        self.assertEqual((0, 1, 10, 10), geometry.fill_rect)
        self.assertEqual((0, 1, 10, 3), geometry.highlight_rect)

    def test_value_bar_geometry_omits_fill_when_ratio_is_zero_or_negative(self) -> None:
        zero = value_bar_geometry((0, 0, 120, 30), ratio=0, min_bar_height=10)
        negative = value_bar_geometry((0, 0, 120, 30), ratio=-0.5, min_bar_height=10)

        self.assertIsNone(zero.fill_rect)
        self.assertIsNone(zero.highlight_rect)
        self.assertIsNone(negative.fill_rect)
        self.assertIsNone(negative.highlight_rect)

    def test_value_bar_highlight_color_brightens_without_overflow(self) -> None:
        self.assertEqual((76, 251, 147), value_bar_highlight_color((36, 211, 107)))
        self.assertEqual((255, 255, 255), value_bar_highlight_color((250, 255, 251)))


if __name__ == "__main__":
    unittest.main()
