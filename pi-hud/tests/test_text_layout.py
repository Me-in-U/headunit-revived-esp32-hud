from __future__ import annotations

import unittest

from hud_pi.text_layout import (
    aligned_surface_rect,
    dimmed_unit_color,
    localized_element_text,
    unit_font_size,
    value_label_rect,
    value_label_text,
    value_unit_positions,
)


class TextLayoutTest(unittest.TestCase):
    def test_unit_font_size_is_half_of_value_size_with_minimum(self) -> None:
        self.assertEqual(12, unit_font_size(18))
        self.assertEqual(20, unit_font_size(40))

    def test_dimmed_unit_color_reduces_each_channel_without_underflow(self) -> None:
        self.assertEqual((60, 0, 215), dimmed_unit_color((100, 20, 255)))

    def test_value_unit_positions_preserve_renderer_alignment_rules(self) -> None:
        layout = value_unit_positions(
            rect=(100, 20, 300, 80),
            prefix_size=(30, 40),
            value_size=(90, 40),
            unit_size=(50, 20),
            spacing=4,
            align="center",
        )

        self.assertEqual(163, layout.start_x)
        self.assertEqual((163, 40), layout.prefix_pos)
        self.assertEqual((193, 40), layout.value_pos)
        self.assertEqual((287, 50), layout.unit_pos)
        self.assertEqual(174, layout.total_width)

    def test_value_unit_positions_support_right_alignment_without_prefix(self) -> None:
        layout = value_unit_positions(
            rect=(10, 10, 160, 60),
            prefix_size=None,
            value_size=(70, 32),
            unit_size=(24, 16),
            spacing=4,
            align="right",
        )

        self.assertIsNone(layout.prefix_pos)
        self.assertEqual(72, layout.start_x)
        self.assertEqual((72, 24), layout.value_pos)
        self.assertEqual((146, 32), layout.unit_pos)

    def test_aligned_surface_rect_matches_renderer_text_anchor_rules(self) -> None:
        rect = (100, 20, 300, 80)
        surface_size = (40, 16)

        self.assertEqual((100, 52, 40, 16), aligned_surface_rect(rect, surface_size, "left"))
        self.assertEqual((230, 52, 40, 16), aligned_surface_rect(rect, surface_size, "center"))
        self.assertEqual((360, 52, 40, 16), aligned_surface_rect(rect, surface_size, "right"))
        self.assertEqual((100, 52, 40, 16), aligned_surface_rect(rect, surface_size, "unknown"))

    def test_localized_element_text_uses_language_then_default_then_key_fallback(self) -> None:
        element = {
            "text": "READY",
            "label": "Status",
            "text_i18n": {"ko": "준비", "en": "READY"},
            "prefix_i18n": {"ko": "속도 "},
        }

        self.assertEqual("준비", localized_element_text(element, "text", "ko", "Status"))
        self.assertEqual("READY", localized_element_text(element, "text", "ja", "Status"))
        self.assertEqual("속도 ", localized_element_text(element, "prefix", "ko", ""))
        self.assertEqual("Status", localized_element_text(element, "label", "ko", "Fallback"))
        self.assertEqual("Fallback", localized_element_text(element, "missing", "ko", "Fallback"))

    def test_value_label_helpers_match_renderer_label_text_and_rect_rules(self) -> None:
        element = {
            "prefix": "RPM ",
            "suffix": " x1000",
            "prefix_i18n": {"ko": "회전 "},
            "suffix_i18n": {"ko": " 천"},
        }

        self.assertEqual("회전 3 천", value_label_text(element, "3", "ko"))
        self.assertEqual((20, 120, 360, 60), value_label_rect((20, 40, 360, 180), y=120))
        self.assertEqual((20, 120, 360, 1), value_label_rect((20, 40, 360, 2), y=120))


if __name__ == "__main__":
    unittest.main()
