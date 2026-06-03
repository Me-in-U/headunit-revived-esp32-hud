from __future__ import annotations

import unittest

from hud_pi.layout_values import (
    choice_or_default,
    color_tuple,
    int_or_default,
    is_hex_color,
    maybe_number,
    number_or_default,
    positive_int,
    string_or_default,
)


class LayoutValuesTest(unittest.TestCase):
    def test_color_tuple_accepts_short_and_long_hex_with_fallback(self) -> None:
        self.assertEqual((170, 187, 204), color_tuple("#abc"))
        self.assertEqual((18, 52, 86), color_tuple("#123456"))
        self.assertEqual((1, 2, 3), color_tuple("blue", (1, 2, 3)))
        self.assertTrue(is_hex_color("#ABCDEF"))
        self.assertFalse(is_hex_color("#12345"))

    def test_numeric_and_choice_helpers_normalize_layout_values(self) -> None:
        self.assertEqual(42, int_or_default("42", 0))
        self.assertEqual(1, positive_int("-5", 9))
        self.assertIsNone(maybe_number(True))
        self.assertEqual(12, number_or_default("12.0", 0))
        self.assertEqual(12.5, number_or_default("12.5", 0))
        self.assertEqual("fallback", string_or_default("   ", "fallback"))
        self.assertEqual("center", choice_or_default(" CENTER ", {"left", "center", "right"}, "left"))


if __name__ == "__main__":
    unittest.main()
