from __future__ import annotations

import unittest

from hud_pi.font_config import CJK_FONT_CANDIDATES, FontRequest, font_request


class FontConfigTest(unittest.TestCase):
    def test_font_request_uses_builtin_for_default_non_cjk_language(self) -> None:
        self.assertEqual(FontRequest("builtin", None), font_request("default", "en"))
        self.assertEqual(FontRequest("builtin", None), font_request("", "en"))

    def test_font_request_uses_cjk_candidates_for_default_korean_language(self) -> None:
        request = font_request("default", "ko")

        self.assertEqual("system", request.backend)
        self.assertIsNotNone(request.family)
        self.assertIn("Noto Sans CJK KR", request.family or "")
        self.assertIn("Malgun Gothic", request.family or "")
        self.assertIn("Noto Sans CJK KR", CJK_FONT_CANDIDATES)

    def test_font_request_uses_explicit_family_for_all_languages(self) -> None:
        self.assertEqual(FontRequest("system", "Verdana"), font_request("Verdana", "en"))
        self.assertEqual(FontRequest("system", "Verdana"), font_request("Verdana", "ko"))


if __name__ == "__main__":
    unittest.main()
