from __future__ import annotations

import unittest

from hud_pi.warning_icon_state import warning_icon_presentation


class WarningIconStateTest(unittest.TestCase):
    def test_inactive_icon_without_show_when_inactive_is_hidden(self) -> None:
        presentation = warning_icon_presentation(
            {"id": "door", "binding": "warnings.door_open"},
            lambda _binding, fallback: fallback,
        )

        self.assertFalse(presentation.visible)
        self.assertFalse(presentation.active)
        self.assertEqual("door", presentation.icon_name)

    def test_active_icon_uses_warning_color_and_full_alpha(self) -> None:
        presentation = warning_icon_presentation(
            {"id": "door", "icon": "door_open", "binding": "warnings.door_open", "warning_color": "#ffaa00"},
            lambda _binding, _fallback: True,
        )

        self.assertTrue(presentation.visible)
        self.assertTrue(presentation.active)
        self.assertEqual("door_open", presentation.icon_name)
        self.assertEqual((255, 170, 0), presentation.tint_color)
        self.assertEqual(255, presentation.alpha)

    def test_inactive_visible_icon_uses_inactive_color_and_alpha(self) -> None:
        presentation = warning_icon_presentation(
            {
                "id": "abs",
                "binding": "warnings.abs",
                "show_when_inactive": True,
                "inactive_color": "#123456",
                "inactive_alpha": 42,
            },
            lambda _binding, fallback: fallback,
        )

        self.assertTrue(presentation.visible)
        self.assertFalse(presentation.active)
        self.assertEqual((18, 52, 86), presentation.tint_color)
        self.assertEqual(42, presentation.alpha)


if __name__ == "__main__":
    unittest.main()
