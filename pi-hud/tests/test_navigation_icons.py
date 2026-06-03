from __future__ import annotations

import unittest

from hud_pi.navigation_icons import fallback_symbol, maneuver_icon_name


class NavigationIconsTest(unittest.TestCase):
    def test_maneuver_icon_name_maps_event_and_turn_side_to_asset_name(self) -> None:
        self.assertEqual("flag", maneuver_icon_name(15, 3))
        self.assertEqual("roundabout_left", maneuver_icon_name(10, 1))
        self.assertEqual("roundabout_right", maneuver_icon_name(11, 2))
        self.assertEqual("roundabout_right", maneuver_icon_name(12, 3))
        self.assertEqual("straight", maneuver_icon_name(14, 3))
        self.assertEqual("u_turn_left", maneuver_icon_name(6, 1))
        self.assertEqual("u_turn_right", maneuver_icon_name(6, 2))
        self.assertEqual("turn_left", maneuver_icon_name(4, 1))
        self.assertEqual("turn_right", maneuver_icon_name(4, 2))
        self.assertEqual("straight", maneuver_icon_name(4, 3))

    def test_fallback_symbol_matches_renderer_drawing_branches(self) -> None:
        self.assertEqual("destination", fallback_symbol(15, 3))
        self.assertEqual("roundabout", fallback_symbol(10, 1))
        self.assertEqual("roundabout", fallback_symbol(11, 2))
        self.assertEqual("roundabout", fallback_symbol(12, 3))
        self.assertEqual("straight", fallback_symbol(14, 3))
        self.assertEqual("uturn", fallback_symbol(6, 1))
        self.assertEqual("turn_left", fallback_symbol(4, 1))
        self.assertEqual("turn_right", fallback_symbol(4, 2))
        self.assertEqual("straight", fallback_symbol(4, 3))


if __name__ == "__main__":
    unittest.main()
