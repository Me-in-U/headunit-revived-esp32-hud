from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal, cast

from .display_format import DEFAULT_LANGUAGE, format_value
from .text_layout import localized_element_text


TextualRenderAction = Literal["text", "bar", "analog", "needle", "sport_gauge"]
SPECIAL_VALUE_RENDER_ACTIONS = {"bar", "analog", "needle", "sport_gauge"}


@dataclass(frozen=True)
class TextualPresentation:
    is_value: bool
    raw_value: Any
    value: str
    value_style: str
    prefix: str
    suffix: str
    text: str
    uses_unit_layout: bool


def textual_presentation(
    element: dict[str, Any],
    resolve_first: Callable[[list[Any], Any], Any],
    language: str,
) -> TextualPresentation:
    if element.get("type") == "value":
        bindings = [element.get("binding", "")] + list(element.get("fallback_bindings", []))
        raw_value = resolve_first(bindings, "--")
        value = format_value(raw_value, language=language)
        prefix = localized_element_text(element, "prefix", language, "", default_language=DEFAULT_LANGUAGE)
        suffix = localized_element_text(element, "suffix", language, "", default_language=DEFAULT_LANGUAGE)
        return TextualPresentation(
            is_value=True,
            raw_value=raw_value,
            value=value,
            value_style=str(element.get("value_style", "digital")),
            prefix=prefix,
            suffix=suffix,
            text=f"{prefix}{value}{suffix}",
            uses_unit_layout=bool(suffix and value != "--"),
        )
    text = localized_element_text(
        element,
        "text",
        language,
        element.get("label", ""),
        default_language=DEFAULT_LANGUAGE,
    )
    return TextualPresentation(
        is_value=False,
        raw_value=None,
        value="",
        value_style="digital",
        prefix="",
        suffix="",
        text=text,
        uses_unit_layout=False,
    )


def textual_render_action(presentation: TextualPresentation) -> TextualRenderAction:
    if not presentation.is_value:
        return "text"
    if presentation.value_style in SPECIAL_VALUE_RENDER_ACTIONS:
        return cast(TextualRenderAction, presentation.value_style)
    return "text"
