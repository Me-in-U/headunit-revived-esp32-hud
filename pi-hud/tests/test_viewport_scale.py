from __future__ import annotations

import unittest

from hud_pi.viewport_scale import element_rect, scale_size, scale_x_value, scale_y_value, viewport_scale


class ViewportScaleTest(unittest.TestCase):
    def test_viewport_scale_uses_screen_to_canvas_ratios(self) -> None:
        scale = viewport_scale(screen_size=(960, 240), canvas_size=(1920, 480))

        self.assertEqual(0.5, scale.x)
        self.assertEqual(0.5, scale.y)

    def test_scale_axis_and_size_match_renderer_rules(self) -> None:
        scale = viewport_scale(screen_size=(960, 120), canvas_size=(1920, 480))

        self.assertEqual(50, scale_x_value(100, scale))
        self.assertEqual(25, scale_y_value(100, scale))
        self.assertEqual(25, scale_size(100, scale))
        self.assertEqual(1, scale_size(0, scale))

    def test_element_rect_uses_renderer_defaults_and_axis_scaling(self) -> None:
        scale = viewport_scale(screen_size=(960, 120), canvas_size=(1920, 480))

        self.assertEqual((5, 5, 50, 10), element_rect({"x": 10, "y": 20, "w": 100, "h": 40}, scale))
        self.assertEqual((0, 0, 50, 10), element_rect({}, scale))


if __name__ == "__main__":
    unittest.main()
