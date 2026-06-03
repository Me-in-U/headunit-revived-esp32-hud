from __future__ import annotations

import os
from typing import Any

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from .display_format import DEFAULT_LANGUAGE
from .gauge_geometry import element_value_ratio
from .icon_assets import NAV_ICON_DIR, WARNING_ICON_DIR
from .pygame_font_loader import load_cached_font
from .pygame_icon_loader import load_cached_png_icon
from .pygame_image_loader import load_cached_image_source
from .text_fit import fit_text_surface as fit_text_surface_for_rect
from .viewport_scale import ViewportScale, element_rect, scale_size, scale_x_value, scale_y_value


class RendererSupportMixin:
    canvas: dict[str, Any]
    viewport_scale: ViewportScale
    font_cache: dict[tuple[int, str, str, str, str], pygame.font.Font]
    warning_icon_cache: dict[str, pygame.Surface]
    nav_icon_cache: dict[str, pygame.Surface]
    background_image_cache: tuple[str, pygame.Surface] | None
    language: str

    def _load_background_image(self) -> pygame.Surface | None:
        image, self.background_image_cache = load_cached_image_source(
            self.canvas.get("background_image"),
            self.background_image_cache,
        )
        return image

    def _font(
        self,
        size: int,
        family: str = "default",
        weight: str = "normal",
        style: str = "normal",
        language: str | None = None,
    ) -> pygame.font.Font:
        return load_cached_font(
            self.font_cache,
            size,
            family,
            weight,
            style,
            language or getattr(self, "language", DEFAULT_LANGUAGE),
            scale_size=self._s,
        )

    def _rect(self, element: dict[str, Any]) -> pygame.Rect:
        return pygame.Rect(element_rect(element, self._scale()))

    def _rect_tuple(self, rect: pygame.Rect) -> tuple[int, int, int, int]:
        return (rect.x, rect.y, rect.width, rect.height)

    def _value_ratio(self, raw_value: Any, element: dict[str, Any]) -> float:
        return element_value_ratio(raw_value, element)

    def _fit_text_surface(self, text: str, element: dict[str, Any], rect: pygame.Rect, color: tuple[int, int, int]) -> pygame.Surface:
        return fit_text_surface_for_rect(
            text,
            element,
            rect,
            color,
            lambda size, family, weight, style: self._font(size, family, weight, style, language=self.language),
        )

    def _load_warning_icon(self, icon_name: str) -> pygame.Surface | None:
        return load_cached_png_icon(icon_name, WARNING_ICON_DIR, self.warning_icon_cache)

    def _load_nav_icon(self, icon_name: str) -> pygame.Surface | None:
        return load_cached_png_icon(icon_name, NAV_ICON_DIR, self.nav_icon_cache)

    def _x(self, value: float | int) -> int:
        return scale_x_value(value, self._scale())

    def _y(self, value: float | int) -> int:
        return scale_y_value(value, self._scale())

    def _s(self, value: float | int) -> int:
        return scale_size(value, self._scale())

    def _scale(self) -> ViewportScale:
        return self.viewport_scale
