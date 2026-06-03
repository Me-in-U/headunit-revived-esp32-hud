from __future__ import annotations

import unittest

from hud_pi.display_format import (
    DEFAULT_LANGUAGE,
    format_value,
    normalize_language,
    warning_active_color,
    warning_label,
)


class DisplayFormatTest(unittest.TestCase):
    def test_normalize_language_accepts_known_prefixes_and_fallback(self) -> None:
        self.assertEqual("en", DEFAULT_LANGUAGE)
        self.assertEqual("ko", normalize_language("ko-KR"))
        self.assertEqual("en", normalize_language("en-US"))
        self.assertEqual("ko", normalize_language("fr", fallback="ko"))
        self.assertEqual("en", normalize_language("fr", fallback="jp"))

    def test_format_value_localizes_status_values(self) -> None:
        self.assertEqual("ON", format_value(True))
        self.assertEqual("OFF", format_value(False))
        self.assertEqual("NONE", format_value([]))
        self.assertEqual("켜짐", format_value(True, language="ko"))
        self.assertEqual("꺼짐", format_value(False, language="ko"))
        self.assertEqual("없음", format_value([], language="ko"))
        self.assertEqual("P0133, U0100", format_value(["P0133", "U0100"]))

    def test_warning_label_and_color_use_known_warning_maps_with_fallbacks(self) -> None:
        self.assertEqual("DOOR", warning_label("warnings.door_open", "en"))
        self.assertEqual("도어", warning_label("warnings.door_open", "ko"))
        self.assertEqual("CUSTOM", warning_label("warnings.custom", "ko"))
        self.assertEqual("#ee2024", warning_active_color("warnings.door_open"))
        self.assertEqual("#ff3b30", warning_active_color("warnings.custom"))


if __name__ == "__main__":
    unittest.main()
