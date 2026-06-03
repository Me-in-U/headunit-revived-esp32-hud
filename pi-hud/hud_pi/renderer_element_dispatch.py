from __future__ import annotations

from typing import Any

import pygame

from .element_rendering import render_action, sorted_visible_elements
from .pygame_layer import render_alpha_layer


class RendererElementDispatchMixin:
    screen: pygame.Surface

    def _render_elements(self, elements: list[dict[str, Any]], state: Any) -> None:
        for element in sorted_visible_elements(elements):
            action = render_action(element)
            if action == "warning_row":
                self._draw_warning_row(element, state)
            elif action == "warning_icon":
                self._draw_warning_icon(element, state)
            elif action == "nav_icon":
                self._draw_nav_icon(element, state)
            elif action == "gear_indicator":
                self._draw_gear_indicator(element, state)
            else:
                self._draw_textual(element, state)

    def _render_elements_layer(self, elements: list[dict[str, Any]], state: Any, alpha: int) -> None:
        target = self.screen

        def render_layer(layer: pygame.Surface) -> None:
            original_screen = self.screen
            self.screen = layer
            try:
                self._render_elements(elements, state)
            finally:
                self.screen = original_screen

        render_alpha_layer(target, alpha, render_layer)
