from __future__ import annotations

import unittest

from hud_pi.icon_assets import (
    MATERIAL_NAV_ICON_SOURCE,
    NAV_ICON_DIR,
    WARNING_ICON_DIR,
    clean_icon_name,
    icon_filename,
)


class IconAssetsTest(unittest.TestCase):
    def test_clean_icon_name_matches_renderer_asset_key_rules(self) -> None:
        self.assertEqual("turn_right", clean_icon_name(" Turn Right "))
        self.assertEqual("u-turn_left", clean_icon_name("U-Turn Left"))
        self.assertEqual("___turn_right", clean_icon_name("../turn/right"))
        self.assertEqual("", clean_icon_name("   "))

    def test_icon_filename_uses_clean_name_and_png_suffix(self) -> None:
        self.assertEqual("turn_right.png", icon_filename(" Turn Right "))
        self.assertEqual("", icon_filename("   "))

    def test_icon_asset_constants_point_to_existing_runtime_dirs(self) -> None:
        self.assertTrue(WARNING_ICON_DIR.is_dir())
        self.assertTrue(NAV_ICON_DIR.is_dir())
        self.assertIn("@material-design-icons/svg", MATERIAL_NAV_ICON_SOURCE)


if __name__ == "__main__":
    unittest.main()
