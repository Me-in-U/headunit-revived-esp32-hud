from __future__ import annotations

import unittest

from hud_pi.nav_icon_state import nav_icon_presentation


class NavIconStateTest(unittest.TestCase):
    def test_nav_icon_presentation_resolves_numeric_fields_and_active_colors(self) -> None:
        values = {"nav.event_type": "10", "nav.turn_side": "1", "nav.connected": True}
        presentation = nav_icon_presentation(
            {
                "event_binding": "nav.event_type",
                "side_binding": "nav.turn_side",
                "color": "#010203",
                "accent": "#0a0b0c",
                "inactive_color": "#111213",
            },
            lambda binding, fallback: values.get(binding, fallback),
        )

        self.assertEqual(10, presentation.event_type)
        self.assertEqual(1, presentation.turn_side)
        self.assertEqual("roundabout_left", presentation.icon_name)
        self.assertEqual("roundabout", presentation.fallback_symbol)
        self.assertTrue(presentation.active)
        self.assertEqual((1, 2, 3), presentation.draw_color)
        self.assertEqual((10, 11, 12), presentation.destination_dot_color)

    def test_nav_icon_presentation_uses_inactive_color_when_navigation_is_disconnected(self) -> None:
        values = {"nav.event_type": 15, "nav.turn_side": 3, "nav.connected": False}
        presentation = nav_icon_presentation(
            {"color": "#ffffff", "accent": "#00ff00", "inactive_color": "#123456"},
            lambda binding, fallback: values.get(binding, fallback),
        )

        self.assertEqual("flag", presentation.icon_name)
        self.assertEqual("destination", presentation.fallback_symbol)
        self.assertFalse(presentation.active)
        self.assertEqual((18, 52, 86), presentation.draw_color)
        self.assertEqual((18, 52, 86), presentation.destination_dot_color)

    def test_nav_icon_presentation_falls_back_for_invalid_numeric_state(self) -> None:
        values = {"nav.event_type": "bad", "nav.turn_side": None, "nav.connected": True}
        presentation = nav_icon_presentation({}, lambda binding, fallback: values.get(binding, fallback))

        self.assertEqual(0, presentation.event_type)
        self.assertEqual(3, presentation.turn_side)
        self.assertEqual("straight", presentation.icon_name)
        self.assertEqual("straight", presentation.fallback_symbol)


if __name__ == "__main__":
    unittest.main()
