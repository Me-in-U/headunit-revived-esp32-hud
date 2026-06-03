from __future__ import annotations

import unittest

from hud_pi.background_layout import background_target_rect


class BackgroundLayoutTest(unittest.TestCase):
    def test_background_target_rect_supports_cover_contain_and_stretch(self) -> None:
        self.assertEqual((0, -240, 1920, 960), background_target_rect((1920, 480), (800, 400), "cover"))
        self.assertEqual((480, 0, 960, 480), background_target_rect((1920, 480), (800, 400), "contain"))
        self.assertEqual((0, 0, 1920, 480), background_target_rect((1920, 480), (800, 400), "stretch"))

    def test_background_target_rect_falls_back_to_cover_and_handles_invalid_image_size(self) -> None:
        self.assertEqual((0, -240, 1920, 960), background_target_rect((1920, 480), (800, 400), "unknown"))
        self.assertEqual((0, 0, 1920, 480), background_target_rect((1920, 480), (0, 400), "contain"))
        self.assertEqual((0, 0, 1920, 480), background_target_rect((1920, 480), (800, 0), "cover"))


if __name__ == "__main__":
    unittest.main()
