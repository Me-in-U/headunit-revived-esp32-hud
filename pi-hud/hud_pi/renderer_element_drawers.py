from __future__ import annotations

from typing import Any

import pygame

from .display_format import DEFAULT_LANGUAGE
from .pygame_background import draw_canvas_background
from .pygame_gear_indicator import draw_gear_indicator_element
from .pygame_nav_icon import draw_nav_icon_element
from .pygame_textual_rendering import draw_textual_element
from .pygame_value_rendering import draw_value_style_element
from .pygame_warning_icon import draw_warning_icon_element
from .pygame_warning_row import draw_warning_row_element


class RendererElementDrawersMixin:
    screen: pygame.Surface
    canvas: dict[str, Any]
    language: str

    def _draw_background(self) -> None:
        draw_canvas_background(self.screen, self.canvas, self._load_background_image())

    def _draw_textual(self, element: dict[str, Any], state: Any) -> None:
        rect = self._rect(element)
        draw_textual_element(
            self.screen,
            element,
            resolve_first=state.resolve_first,
            rect=self._rect_tuple(rect),
            language=self.language,
            default_language=DEFAULT_LANGUAGE,
            font_factory=lambda size, family, weight, style: self._font(size, family, weight, style, language=self.language),
            scale_y=self._y,
            scale_size=self._s,
            fit_surface=self._fit_text_surface,
        )

    def _draw_value_bar(self, element: dict[str, Any], raw_value: Any, value: str) -> None:
        self._draw_value_style(element, raw_value, value, "bar")

    def _draw_value_analog(self, element: dict[str, Any], raw_value: Any, value: str) -> None:
        self._draw_value_style(element, raw_value, value, "analog")

    def _draw_value_needle(self, element: dict[str, Any], raw_value: Any, value: str) -> None:
        self._draw_value_style(element, raw_value, value, "needle")

    def _draw_value_sport_gauge(self, element: dict[str, Any], raw_value: Any, value: str) -> None:
        self._draw_value_style(element, raw_value, value, "sport_gauge")

    def _draw_value_style(self, element: dict[str, Any], raw_value: Any, value: str, style: str) -> None:
        rect = self._rect(element)
        draw_value_style_element(
            self.screen,
            element,
            rect=self._rect_tuple(rect),
            raw_value=raw_value,
            value=value,
            style=style,
            font_factory=lambda size, family, weight, style: self._font(size, family, weight, style),
            scale_y=self._y,
            scale_size=self._s,
            language=self.language,
            default_language=DEFAULT_LANGUAGE,
            fit_surface=self._fit_text_surface,
        )

    def _draw_nav_icon(self, element: dict[str, Any], state: Any) -> None:
        rect = self._rect(element)
        if rect.width <= 0 or rect.height <= 0:
            return
        draw_nav_icon_element(
            self.screen,
            element,
            rect=self._rect_tuple(rect),
            resolve=state.resolve,
            icon_loader=self._load_nav_icon,
        )

    def _draw_gear_indicator(self, element: dict[str, Any], state: Any) -> None:
        rect = self._rect(element)
        if rect.width <= 0 or rect.height <= 0:
            return
        draw_gear_indicator_element(
            self.screen,
            element,
            rect=self._rect_tuple(rect),
            resolve=state.resolve,
            font_factory=lambda size, family, weight, style: self._font(size, family, weight, style, language=self.language),
        )

    def _draw_warning_row(self, element: dict[str, Any], state: Any) -> None:
        rect = self._rect(element)
        if rect.width <= 0 or rect.height <= 0:
            return
        draw_warning_row_element(
            self.screen,
            element,
            rect=self._rect_tuple(rect),
            active_resolver=lambda binding: state.resolve(binding, False),
            language=self.language,
            font_factory=lambda size, family, weight, style: self._font(size, family, weight, style, language=self.language),
            scale_x=self._x,
        )

    def _draw_warning_icon(self, element: dict[str, Any], state: Any) -> None:
        rect = self._rect(element)
        if rect.width <= 0 or rect.height <= 0:
            return
        draw_warning_icon_element(
            self.screen,
            element,
            rect=self._rect_tuple(rect),
            resolve=state.resolve,
            icon_loader=self._load_warning_icon,
        )
