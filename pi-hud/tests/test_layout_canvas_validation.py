from __future__ import annotations

import unittest

from hud_pi.layout_canvas_validation import validate_canvas


class LayoutCanvasValidationTest(unittest.TestCase):
    def test_canvas_validation_preserves_size_and_color_errors(self) -> None:
        errors = validate_canvas({"width": 0, "height": -1, "background": "white"})

        self.assertEqual(
            [
                "canvas width and height must be positive",
                "canvas background color 'white' must be #RGB or #RRGGBB",
            ],
            errors,
        )


if __name__ == "__main__":
    unittest.main()
