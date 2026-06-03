from __future__ import annotations

import os
import time
from typing import Any

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from .display_format import DEFAULT_LANGUAGE, format_value, normalize_language
from .icon_assets import MATERIAL_NAV_ICON_SOURCE
from .renderer_elements import RendererElementDrawingMixin
from .renderer_support import RendererSupportMixin
from .screen_flow import (
    ScreenTransitionState,
    active_screen_name,
    advance_screen_transition,
    elements_for_screen,
    fade_active,
    fade_progress,
)
from .state import HudState
from .viewport_scale import viewport_scale


class HudRenderer(RendererElementDrawingMixin, RendererSupportMixin):
    def __init__(self, layout: dict[str, Any], screen: pygame.Surface, language: str | None = None) -> None:
        pygame.font.init()
        self.layout = layout
        self.screen = screen
        self.canvas = layout["canvas"]
        self.language = normalize_language(language or layout.get("language") or DEFAULT_LANGUAGE)
        self.viewport_scale = viewport_scale(
            (screen.get_width(), screen.get_height()),
            (self.canvas["width"], self.canvas["height"]),
        )
        self.font_cache: dict[tuple[int, str, str, str, str], pygame.font.Font] = {}
        self.warning_icon_cache: dict[str, pygame.Surface] = {}
        self.nav_icon_cache: dict[str, pygame.Surface] = {}
        self.background_image_cache: tuple[str, pygame.Surface] | None = None
        self.active_screen_name: str | None = None
        self.previous_screen_name: str | None = None
        self.transition_started_at = 0.0

    def render(self, state: HudState) -> None:
        self._draw_background()
        screen_name = active_screen_name(self.layout, nav_connected=bool(state.resolve("nav.connected", False)))
        now = time.monotonic()
        transition = advance_screen_transition(
            ScreenTransitionState(
                active_screen_name=self.active_screen_name,
                previous_screen_name=self.previous_screen_name,
                transition_started_at=self.transition_started_at,
            ),
            screen_name,
            now=now,
        )
        self.active_screen_name = transition.active_screen_name
        self.previous_screen_name = transition.previous_screen_name
        self.transition_started_at = transition.transition_started_at

        if fade_active(
            self.layout,
            previous_screen_name=self.previous_screen_name,
            transition_started_at=self.transition_started_at,
            now=now,
        ):
            progress = fade_progress(self.layout, transition_started_at=self.transition_started_at, now=now)
            self._render_elements_layer(elements_for_screen(self.layout, self.previous_screen_name), state, int(255 * (1.0 - progress)))
            self._render_elements_layer(elements_for_screen(self.layout, self.active_screen_name), state, int(255 * progress))
            return
        self.previous_screen_name = None
        self._render_elements(elements_for_screen(self.layout, self.active_screen_name), state)
