from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from hud_pi.pygame_font_loader import load_cached_font


class PygameFontLoaderTest(unittest.TestCase):
    def test_load_cached_font_uses_builtin_font_for_default_english_and_caches_it(self) -> None:
        cache = {}
        font = Mock()

        with patch("hud_pi.pygame_font_loader.pygame.font.Font", return_value=font) as builtin_font:
            first = load_cached_font(cache, 6, family="", weight="bold", style="italic", language="en", scale_size=lambda size: size)
            second = load_cached_font(cache, 6, family="", weight="bold", style="italic", language="en", scale_size=lambda size: size)

        self.assertIs(first, font)
        self.assertIs(second, font)
        builtin_font.assert_called_once_with(None, 8)
        font.set_bold.assert_called_once_with(True)
        font.set_italic.assert_called_once_with(True)

    def test_load_cached_font_uses_system_font_for_explicit_family(self) -> None:
        cache = {}
        font = Mock()

        with patch("hud_pi.pygame_font_loader.pygame.font.SysFont", return_value=font) as system_font:
            result = load_cached_font(cache, 24, family="Verdana", weight="normal", style="normal", language="ko", scale_size=lambda size: size * 2)

        self.assertIs(result, font)
        system_font.assert_called_once_with("Verdana", 48, bold=False, italic=False)


if __name__ == "__main__":
    unittest.main()
