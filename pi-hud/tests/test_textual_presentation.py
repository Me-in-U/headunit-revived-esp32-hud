from __future__ import annotations

import unittest
from typing import Any

from hud_pi.textual_presentation import TextualPresentation, textual_presentation, textual_render_action


class TextualPresentationTest(unittest.TestCase):
    def test_value_presentation_uses_first_available_binding_and_localized_units(self) -> None:
        element = {
            "type": "value",
            "binding": "vehicle.speed_kmh",
            "fallback_bindings": ["vehicle.speed_kmh_backup"],
            "value_style": "digital",
            "prefix": "",
            "prefix_i18n": {"ko": "속도 "},
            "suffix": " km/h",
        }

        presentation = textual_presentation(
            element,
            lambda bindings, fallback: _resolve_first(bindings, fallback, {"vehicle.speed_kmh_backup": 57}),
            "ko",
        )

        self.assertTrue(presentation.is_value)
        self.assertEqual(57, presentation.raw_value)
        self.assertEqual("57", presentation.value)
        self.assertEqual("digital", presentation.value_style)
        self.assertEqual("속도 ", presentation.prefix)
        self.assertEqual(" km/h", presentation.suffix)
        self.assertEqual("속도 57 km/h", presentation.text)
        self.assertTrue(presentation.uses_unit_layout)

    def test_value_presentation_does_not_use_unit_layout_for_missing_value(self) -> None:
        presentation = textual_presentation(
            {"type": "value", "binding": "vehicle.speed_kmh", "suffix": " km/h"},
            lambda _bindings, fallback: fallback,
            "en",
        )

        self.assertEqual("--", presentation.value)
        self.assertFalse(presentation.uses_unit_layout)

    def test_text_presentation_uses_localized_text_and_label_fallback(self) -> None:
        presentation = textual_presentation(
            {"type": "text", "label": "Status", "text_i18n": {"ko": "준비"}},
            lambda _bindings, fallback: fallback,
            "ko",
        )

        self.assertFalse(presentation.is_value)
        self.assertIsNone(presentation.raw_value)
        self.assertEqual("", presentation.value)
        self.assertEqual("", presentation.prefix)
        self.assertEqual("", presentation.suffix)
        self.assertEqual("준비", presentation.text)

    def test_textual_render_action_routes_only_special_value_styles(self) -> None:
        self.assertEqual("text", textual_render_action(_presentation(is_value=False, value_style="bar")))
        self.assertEqual("text", textual_render_action(_presentation(is_value=True, value_style="digital")))
        self.assertEqual("bar", textual_render_action(_presentation(is_value=True, value_style="bar")))
        self.assertEqual("analog", textual_render_action(_presentation(is_value=True, value_style="analog")))
        self.assertEqual("needle", textual_render_action(_presentation(is_value=True, value_style="needle")))
        self.assertEqual("sport_gauge", textual_render_action(_presentation(is_value=True, value_style="sport_gauge")))
        self.assertEqual("text", textual_render_action(_presentation(is_value=True, value_style="unknown")))


def _resolve_first(bindings: list[Any], fallback: Any, values: dict[str, Any]) -> Any:
    for binding in bindings:
        value = values.get(str(binding))
        if value is not None:
            return value
    return fallback


def _presentation(*, is_value: bool, value_style: str) -> TextualPresentation:
    return TextualPresentation(
        is_value=is_value,
        raw_value=None,
        value="",
        value_style=value_style,
        prefix="",
        suffix="",
        text="",
        uses_unit_layout=False,
    )


if __name__ == "__main__":
    unittest.main()
