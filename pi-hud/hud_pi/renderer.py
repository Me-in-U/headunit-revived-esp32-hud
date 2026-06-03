from __future__ import annotations

import base64
import io
import math
import os
import time
from pathlib import Path
from typing import Any

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from .layout import color_tuple
from .state import HudState


DEFAULT_LANGUAGE = "en"
WARNING_ICON_DIR = Path(__file__).resolve().parents[1] / "assets" / "warning-icons"
NAV_ICON_DIR = Path(__file__).resolve().parents[1] / "assets" / "nav-icons"
MATERIAL_NAV_ICON_SOURCE = "@material-design-icons/svg 0.14.15 Apache-2.0 https://github.com/marella/material-design-icons"
GAUGE_START_DEGREES = 135
GAUGE_SWEEP_DEGREES = 270
CJK_FONT_CANDIDATES = (
    "Noto Sans CJK KR",
    "Noto Sans KR",
    "NanumGothic",
    "Malgun Gothic",
    "Apple SD Gothic Neo",
    "Arial Unicode MS",
)

WARNING_LABELS = {
    "en": {
        "warnings.door_open": "DOOR",
        "warnings.battery": "BATT",
        "warnings.brake": "BRAKE",
        "warnings.abs": "ABS",
        "warnings.airbag": "AIR",
        "warnings.oil_pressure": "OIL",
        "warnings.check_engine": "ENG",
        "warnings.eps": "EPS",
        "warnings.coolant_temp": "TEMP",
        "warnings.seatbelt": "BELT",
        "warnings.low_fuel": "FUEL",
        "warnings.tire_pressure": "TIRE",
        "warnings.high_beam": "HIGH",
        "warnings.low_beam": "LOW",
        "warnings.parking_lights": "PARK",
        "warnings.fog_light": "FOG",
        "warnings.washer_fluid": "WASH",
        "warnings.cruise_control": "CRUISE",
        "warnings.traction_control": "TRAC",
        "warnings.glow_plug": "GLOW",
    },
    "ko": {
        "warnings.door_open": "도어",
        "warnings.battery": "배터리",
        "warnings.brake": "브레이크",
        "warnings.abs": "ABS",
        "warnings.airbag": "에어백",
        "warnings.oil_pressure": "오일",
        "warnings.check_engine": "엔진",
        "warnings.eps": "EPS",
        "warnings.coolant_temp": "수온",
        "warnings.seatbelt": "벨트",
        "warnings.low_fuel": "연료",
        "warnings.tire_pressure": "타이어",
        "warnings.high_beam": "상향",
        "warnings.low_beam": "하향",
        "warnings.parking_lights": "미등",
        "warnings.fog_light": "안개등",
        "warnings.washer_fluid": "워셔액",
        "warnings.cruise_control": "크루즈",
        "warnings.traction_control": "구동",
        "warnings.glow_plug": "예열",
    },
}

WARNING_ACTIVE_COLORS = {
    "warnings.door_open": "#ee2024",
    "warnings.battery": "#ee2024",
    "warnings.brake": "#ee2024",
    "warnings.abs": "#ffae00",
    "warnings.airbag": "#ee2024",
    "warnings.oil_pressure": "#ee2024",
    "warnings.check_engine": "#ffae00",
    "warnings.eps": "#ee2024",
    "warnings.coolant_temp": "#ee2024",
    "warnings.seatbelt": "#ee2024",
    "warnings.low_fuel": "#ffae00",
    "warnings.tire_pressure": "#ffae00",
    "warnings.high_beam": "#40a7ff",
    "warnings.low_beam": "#24d36b",
    "warnings.parking_lights": "#24d36b",
    "warnings.fog_light": "#24d36b",
    "warnings.washer_fluid": "#ffae00",
    "warnings.cruise_control": "#24d36b",
    "warnings.traction_control": "#ffae00",
    "warnings.glow_plug": "#ffae00",
}


def normalize_language(language: Any, fallback: str = DEFAULT_LANGUAGE) -> str:
    value = str(language or fallback).strip().lower()
    if value.startswith("ko"):
        return "ko"
    if value.startswith("en"):
        return "en"
    return fallback if fallback in {"ko", "en"} else DEFAULT_LANGUAGE


def format_value(raw_value: Any, language: str = DEFAULT_LANGUAGE) -> str:
    language = normalize_language(language)
    if isinstance(raw_value, bool):
        if language == "ko":
            return "켜짐" if raw_value else "꺼짐"
        return "ON" if raw_value else "OFF"
    if isinstance(raw_value, list):
        if language == "ko":
            return ", ".join(str(item) for item in raw_value) if raw_value else "없음"
        return ", ".join(str(item) for item in raw_value) if raw_value else "NONE"
    return str(raw_value)


class HudRenderer:
    def __init__(self, layout: dict[str, Any], screen: pygame.Surface, language: str | None = None) -> None:
        self.layout = layout
        self.screen = screen
        self.canvas = layout["canvas"]
        self.language = normalize_language(language or layout.get("language") or DEFAULT_LANGUAGE)
        self.scale_x = screen.get_width() / self.canvas["width"]
        self.scale_y = screen.get_height() / self.canvas["height"]
        self.font_cache: dict[tuple[int, str, str, str, str], pygame.font.Font] = {}
        self.warning_icon_cache: dict[str, pygame.Surface] = {}
        self.nav_icon_cache: dict[str, pygame.Surface] = {}
        self.background_image_cache: tuple[str, pygame.Surface] | None = None
        self.active_screen_name: str | None = None
        self.previous_screen_name: str | None = None
        self.transition_started_at = 0.0

    def render(self, state: HudState) -> None:
        self._draw_background()
        screen_name = self._active_screen_name_for_state(state)
        now = time.monotonic()
        if self.active_screen_name is None:
            self.active_screen_name = screen_name
        elif self.active_screen_name != screen_name:
            self.previous_screen_name = self.active_screen_name
            self.active_screen_name = screen_name
            self.transition_started_at = now

        if self._fade_active(now):
            progress = self._fade_progress(now)
            self._render_elements_layer(self._elements_for_screen(self.previous_screen_name), state, int(255 * (1.0 - progress)))
            self._render_elements_layer(self._elements_for_screen(self.active_screen_name), state, int(255 * progress))
            return
        self.previous_screen_name = None
        self._render_elements(self._elements_for_screen(self.active_screen_name), state)

    def _draw_background(self) -> None:
        self.screen.fill(color_tuple(self.canvas.get("background", "#000000"), (0, 0, 0)))
        image = self._load_background_image()
        if image is None:
            return
        target = self._background_target_rect(image)
        scaled = pygame.transform.smoothscale(image, (target.width, target.height))
        self.screen.blit(scaled, target)

    def _background_target_rect(self, image: pygame.Surface) -> pygame.Rect:
        screen_w = self.screen.get_width()
        screen_h = self.screen.get_height()
        fit = str(self.canvas.get("background_image_fit", "cover")).strip().lower()
        if fit == "stretch" or image.get_width() <= 0 or image.get_height() <= 0:
            return pygame.Rect(0, 0, screen_w, screen_h)
        scale = min(screen_w / image.get_width(), screen_h / image.get_height()) if fit == "contain" else max(
            screen_w / image.get_width(), screen_h / image.get_height()
        )
        width = max(1, int(image.get_width() * scale))
        height = max(1, int(image.get_height() * scale))
        return pygame.Rect((screen_w - width) // 2, (screen_h - height) // 2, width, height)

    def _load_background_image(self) -> pygame.Surface | None:
        value = self.canvas.get("background_image")
        if not isinstance(value, str) or not value.strip():
            return None
        source = value.strip()
        if self.background_image_cache and self.background_image_cache[0] == source:
            return self.background_image_cache[1]
        try:
            if source.startswith("data:image/") and ";base64," in source:
                encoded = source.split(";base64,", 1)[1]
                data = base64.b64decode(encoded)
                loaded = pygame.image.load(io.BytesIO(data))
            else:
                path = Path(source)
                if not path.exists():
                    return None
                loaded = pygame.image.load(str(path))
            try:
                loaded = loaded.convert_alpha()
            except pygame.error:
                loaded = loaded.copy()
        except (OSError, ValueError, pygame.error):
            return None
        self.background_image_cache = (source, loaded)
        return loaded

    def _render_elements(self, elements: list[dict[str, Any]], state: HudState) -> None:
        for element in sorted(elements, key=lambda item: item.get("z", 0)):
            if not element.get("visible", True):
                continue
            element_type = element.get("type", "text")
            if element_type == "warning_row":
                self._draw_warning_row(element, state)
            elif element_type == "warning_icon":
                self._draw_warning_icon(element, state)
            elif element_type == "nav_icon":
                self._draw_nav_icon(element, state)
            elif element_type == "gear_indicator":
                self._draw_gear_indicator(element, state)
            else:
                self._draw_textual(element, state)

    def _render_elements_layer(self, elements: list[dict[str, Any]], state: HudState, alpha: int) -> None:
        target = self.screen
        layer = pygame.Surface((target.get_width(), target.get_height()), pygame.SRCALPHA)
        original_screen = self.screen
        self.screen = layer
        try:
            self._render_elements(elements, state)
        finally:
            self.screen = original_screen
        layer.set_alpha(max(0, min(255, alpha)))
        target.blit(layer, (0, 0))

    def _active_screen_name_for_state(self, state: HudState) -> str:
        screens = self.layout.get("screens")
        if not isinstance(screens, dict) or not screens:
            return "default"
        if bool(state.resolve("nav.connected", False)) and "bridge" in screens:
            return "bridge"
        if "standalone" in screens:
            return "standalone"
        return next(iter(screens))

    def _elements_for_screen(self, screen_name: str | None) -> list[dict[str, Any]]:
        if not screen_name or screen_name == "default":
            return list(self.layout.get("elements", []))
        screens = self.layout.get("screens")
        if not isinstance(screens, dict):
            return list(self.layout.get("elements", []))
        screen = screens.get(screen_name)
        if not isinstance(screen, dict):
            return list(self.layout.get("elements", []))
        elements = screen.get("elements")
        return list(elements) if isinstance(elements, list) else list(self.layout.get("elements", []))

    def _fade_active(self, now: float) -> bool:
        if not self.previous_screen_name:
            return False
        transition = self.layout.get("screen_transition", {})
        if not isinstance(transition, dict) or transition.get("type", "fade") != "fade":
            return False
        duration_ms = int(transition.get("duration_ms", 0))
        if duration_ms <= 0:
            return False
        return (now - self.transition_started_at) * 1000 < duration_ms

    def _fade_progress(self, now: float) -> float:
        transition = self.layout.get("screen_transition", {})
        duration_ms = int(transition.get("duration_ms", 0)) if isinstance(transition, dict) else 0
        if duration_ms <= 0:
            return 1.0
        return max(0.0, min(1.0, ((now - self.transition_started_at) * 1000) / duration_ms))

    def _font(
        self,
        size: int,
        family: str = "default",
        weight: str = "normal",
        style: str = "normal",
        language: str | None = None,
    ) -> pygame.font.Font:
        family = family or "default"
        weight = weight or "normal"
        style = style or "normal"
        language = normalize_language(language or getattr(self, "language", DEFAULT_LANGUAGE))
        key = (size, family, weight, style, language)
        if key not in self.font_cache:
            bold = weight == "bold"
            italic = style == "italic"
            scaled_size = max(8, self._s(size))
            if family.strip().lower() == "default":
                if language == "ko":
                    font = pygame.font.SysFont(", ".join(CJK_FONT_CANDIDATES), scaled_size, bold=bold, italic=italic)
                else:
                    font = pygame.font.Font(None, scaled_size)
                    font.set_bold(bold)
                    font.set_italic(italic)
            else:
                font = pygame.font.SysFont(family, scaled_size, bold=bold, italic=italic)
            self.font_cache[key] = font
        return self.font_cache[key]

    def _rect(self, element: dict[str, Any]) -> pygame.Rect:
        return pygame.Rect(
            self._x(element.get("x", 0)),
            self._y(element.get("y", 0)),
            self._x(element.get("w", 100)),
            self._y(element.get("h", 40)),
        )

    def _draw_textual(self, element: dict[str, Any], state: HudState) -> None:
        if element.get("type") == "value":
            bindings = [element.get("binding", "")] + list(element.get("fallback_bindings", []))
            raw_value = state.resolve_first(bindings, "--")
            value = format_value(raw_value, language=self.language)
            value_style = str(element.get("value_style", "digital"))
            if value_style == "bar":
                self._draw_value_bar(element, raw_value, value)
                return
            if value_style == "analog":
                self._draw_value_analog(element, raw_value, value)
                return
            if value_style == "needle":
                self._draw_value_needle(element, raw_value, value)
                return
            if value_style == "sport_gauge":
                self._draw_value_sport_gauge(element, raw_value, value)
                return
            
            prefix = self._localized_element_text(element, "prefix")
            suffix = self._localized_element_text(element, "suffix")
            text = f"{prefix}{value}{suffix}"
        else:
            text = self._localized_element_text(element, "text", element.get("label", ""))
            prefix, suffix = "", ""

        rect = self._rect(element)
        color = color_tuple(element.get("color", "#ffffff"))
        
        # Special handling for value + unit (suffix)
        if element.get("type") == "value" and suffix and value != "--":
            self._draw_value_with_unit(value, prefix, suffix, element, rect, color)
            return

        surface = self._fit_text_surface(text, element, rect, color)
        target = surface.get_rect()
        align = element.get("align", "left")
        if align == "center":
            target.center = rect.center
        elif align == "right":
            target.midright = rect.midright
        else:
            target.midleft = rect.midleft
        self.screen.blit(surface, target)

    def _draw_value_with_unit(self, value: str, prefix: str, suffix: str, element: dict[str, Any], rect: pygame.Rect, color: tuple[int, int, int]) -> None:
        requested_size = int(element.get("font_size", 28))
        unit_size = max(12, requested_size // 2)
        family = element.get("font_family", "default")
        weight = element.get("font_weight", "normal")
        style = element.get("font_style", "normal")
        
        val_font = self._font(requested_size, family, "bold" if element.get("type") == "value" else weight, style, language=self.language)
        unit_font = self._font(unit_size, family, weight, style, language=self.language)
        
        prefix_surf = val_font.render(prefix, True, color) if prefix else None
        val_surf = val_font.render(value, True, color)
        unit_surf = unit_font.render(suffix, True, tuple(max(0, c - 40) for c in color))
        
        total_w = (prefix_surf.get_width() if prefix_surf else 0) + val_surf.get_width() + unit_surf.get_width() + self._s(4)
        total_h = max(val_surf.get_height(), unit_surf.get_height())
        
        align = element.get("align", "left")
        if align == "center":
            start_x = rect.centerx - total_w // 2
        elif align == "right":
            start_x = rect.right - total_w
        else:
            start_x = rect.left
            
        y = rect.centery - total_h // 2
        
        curr_x = start_x
        if prefix_surf:
            self.screen.blit(prefix_surf, (curr_x, rect.centery - prefix_surf.get_height() // 2))
            curr_x += prefix_surf.get_width()
            
        self.screen.blit(val_surf, (curr_x, rect.centery - val_surf.get_height() // 2))
        curr_x += val_surf.get_width() + self._s(4)
        
        # Unit is slightly higher (baseline adjustment)
        self.screen.blit(unit_surf, (curr_x, rect.centery - val_surf.get_height() // 2 + (val_surf.get_height() - unit_surf.get_height()) // 2))

    def _draw_text_panel(self, element: dict[str, Any], rect: pygame.Rect) -> None:
        return

    def _draw_value_bar(self, element: dict[str, Any], raw_value: Any, value: str) -> None:
        rect = self._rect(element)
        if rect.width <= 0 or rect.height <= 0:
            return
        ratio = self._value_ratio(raw_value, element)
        track_color = color_tuple(element.get("inactive_color", "#1a2430"), (26, 36, 48))
        fill_color = color_tuple(element.get("accent", "#24d36b"), (36, 211, 107))
        border_color = color_tuple(element.get("color", "#f6fbff"), (246, 251, 255))
        
        bar_height = max(self._y(10), rect.height // 3)
        bar_rect = pygame.Rect(rect.x, rect.centery - bar_height // 2, rect.width, bar_height)
        
        # Draw track
        pygame.draw.rect(self.screen, track_color, bar_rect, border_radius=bar_height // 2)
        
        # Draw fill with subtle inner highlight
        if ratio > 0:
            fill_width = max(bar_height, int(rect.width * ratio))
            fill_rect = pygame.Rect(bar_rect.x, bar_rect.y, fill_width, bar_height)
            pygame.draw.rect(self.screen, fill_color, fill_rect, border_radius=bar_height // 2)
            
            # Inner highlight for a "glassy" look
            highlight_rect = pygame.Rect(fill_rect.x, fill_rect.y, fill_rect.width, fill_rect.height // 3)
            highlight_color = tuple(min(255, c + 40) for c in fill_color)
            pygame.draw.rect(self.screen, highlight_color, highlight_rect, border_radius=bar_height // 2)

        # Segments
        segment_count = 10
        for index in range(1, segment_count):
            x = bar_rect.x + int(bar_rect.width * index / segment_count)
            pygame.draw.line(self.screen, (0, 0, 0, 60), (x, bar_rect.y), (x, bar_rect.bottom), 1)

        # Border
        pygame.draw.rect(self.screen, border_color, bar_rect, width=max(1, self._s(1)), border_radius=bar_height // 2)
        
        if bool(element.get("show_value_label", False)):
            self._draw_value_label(element, rect, value, y=rect.y + max(0, rect.height // 12))

    def _draw_value_analog(self, element: dict[str, Any], raw_value: Any, value: str) -> None:
        rect = self._rect(element)
        if rect.width <= 0 or rect.height <= 0:
            return
        ratio = self._value_ratio(raw_value, element)
        center = (rect.centerx, rect.centery + rect.height // 8)
        radius = max(8, min(rect.width // 2, int(rect.height * 0.66)))
        
        track_color = color_tuple(element.get("inactive_color", "#1a2430"), (26, 36, 48))
        accent = color_tuple(element.get("accent", "#24d36b"), (36, 211, 107))
        tick_color = color_tuple(element.get("color", "#f6fbff"), (246, 251, 255))
        
        width = max(2, self._s(8))
        start = GAUGE_START_DEGREES
        sweep = GAUGE_SWEEP_DEGREES
        
        # High-res AA Arcs
        self._draw_aa_arc(self.screen, track_color, center, radius, math.radians(start), math.radians(start + sweep), width)
        self._draw_aa_arc(self.screen, accent, center, radius, math.radians(start), math.radians(start + sweep * ratio), width)
        
        # Determine tick intervals
        min_val = self._numeric_value(element.get("min_value", 0)) or 0.0
        max_val = self._numeric_value(element.get("max_value", 100)) or 100.0
        range_val = max_val - min_val
        tick_interval = self._numeric_value(element.get("tick_interval"))
        if not tick_interval or tick_interval <= 0:
            # Auto-calculate a reasonable interval (roughly 10 major ticks)
            magnitude = 10 ** math.floor(math.log10(max(1, range_val)))
            if range_val / magnitude < 3:
                tick_interval = magnitude / 5
            elif range_val / magnitude < 6:
                tick_interval = magnitude / 2
            else:
                tick_interval = magnitude
                
        num_ticks = max(1, int(range_val / tick_interval))
        
        tick_font = self._font(int(element.get("font_size", 28)) // 2, element.get("font_family", "default"), "normal", "normal")
        
        for tick in range(0, num_ticks + 1):
            tick_ratio = tick / num_ticks
            angle = math.radians(start + sweep * tick_ratio)
            outer = (center[0] + int(math.cos(angle) * radius), center[1] + int(math.sin(angle) * radius))
            
            # Major ticks every 2 intervals or if it's the first/last
            is_major = tick % 2 == 0 or tick == 0 or tick == num_ticks
            
            inner_ratio = 0.82 if is_major else 0.90
            inner = (center[0] + int(math.cos(angle) * radius * inner_ratio), center[1] + int(math.sin(angle) * radius * inner_ratio))
            pygame.draw.line(self.screen, tick_color, inner, outer, max(1, self._s(2 if is_major else 1)))
            
            if is_major:
                tick_val = min_val + (tick * tick_interval)
                val_str = f"{int(tick_val)}" if tick_val.is_integer() else f"{tick_val:.1f}"
                text_surf = tick_font.render(val_str, True, tick_color)
                
                # Position text inside the tick
                text_ratio = 0.70
                text_pos = (center[0] + int(math.cos(angle) * radius * text_ratio), center[1] + int(math.sin(angle) * radius * text_ratio))
                self.screen.blit(text_surf, text_surf.get_rect(center=text_pos))
            
        if bool(element.get("show_value_label", False)):
            self._draw_value_label(element, rect, value, y=rect.bottom - max(18, rect.height // 4))

    def _draw_value_needle(self, element: dict[str, Any], raw_value: Any, value: str) -> None:
        rect = self._rect(element)
        if rect.width <= 0 or rect.height <= 0:
            return
        ratio = self._value_ratio(raw_value, element)
        center = (rect.centerx, rect.bottom - max(4, rect.height // 8))
        radius = max(8, min(rect.width // 2, int(rect.height * 0.78)))
        
        track_color = color_tuple(element.get("inactive_color", "#1a2430"), (26, 36, 48))
        accent = color_tuple(element.get("accent", "#24d36b"), (36, 211, 107))
        needle_color = color_tuple(element.get("color", "#f6fbff"), (246, 251, 255))
        
        width = max(2, self._s(6))
        start = GAUGE_START_DEGREES
        sweep = GAUGE_SWEEP_DEGREES
        
        self._draw_aa_arc(self.screen, track_color, center, radius, math.radians(start), math.radians(start + sweep), width)
        self._draw_aa_arc(self.screen, accent, center, radius, math.radians(start), math.radians(start + sweep * ratio), width)
        
        min_val = self._numeric_value(element.get("min_value", 0)) or 0.0
        max_val = self._numeric_value(element.get("max_value", 100)) or 100.0
        range_val = max_val - min_val
        tick_interval = self._numeric_value(element.get("tick_interval"))
        if not tick_interval or tick_interval <= 0:
            magnitude = 10 ** math.floor(math.log10(max(1, range_val)))
            if range_val / magnitude < 3:
                tick_interval = magnitude / 5
            elif range_val / magnitude < 6:
                tick_interval = magnitude / 2
            else:
                tick_interval = magnitude
                
        num_ticks = max(1, int(range_val / tick_interval))
        tick_font = self._font(int(element.get("font_size", 28)) // 2, element.get("font_family", "default"), "normal", "normal")
        
        for tick in range(0, num_ticks + 1):
            tick_ratio = tick / num_ticks
            tick_angle = math.radians(start + sweep * tick_ratio)
            
            is_major = tick % 2 == 0 or tick == 0 or tick == num_ticks
            
            outer = (center[0] + int(math.cos(tick_angle) * radius * 0.96), center[1] + int(math.sin(tick_angle) * radius * 0.96))
            inner_ratio = 0.84 if is_major else 0.88
            inner = (center[0] + int(math.cos(tick_angle) * radius * inner_ratio), center[1] + int(math.sin(tick_angle) * radius * inner_ratio))
            pygame.draw.line(self.screen, needle_color, inner, outer, max(1, self._s(2 if is_major else 1)))
            
            if is_major:
                tick_val = min_val + (tick * tick_interval)
                val_str = f"{int(tick_val)}" if tick_val.is_integer() else f"{tick_val:.1f}"
                text_surf = tick_font.render(val_str, True, needle_color)
                text_ratio = 0.72
                text_pos = (center[0] + int(math.cos(tick_angle) * radius * text_ratio), center[1] + int(math.sin(tick_angle) * radius * text_ratio))
                self.screen.blit(text_surf, text_surf.get_rect(center=text_pos))
            
        angle = math.radians(start + sweep * ratio)
        end = (center[0] + int(math.cos(angle) * radius * 0.85), center[1] + int(math.sin(angle) * radius * 0.85))
        
        # Shadow for needle
        pygame.draw.line(self.screen, (0, 0, 0, 120), (center[0] + 2, center[1] + 2), (end[0] + 2, end[1] + 2), max(2, self._s(6)))
        pygame.draw.line(self.screen, accent, center, end, max(3, self._s(6)))
        pygame.draw.line(self.screen, needle_color, center, end, max(1, self._s(2)))
        
        pygame.draw.circle(self.screen, needle_color, center, max(4, self._s(8)))
        pygame.draw.circle(self.screen, accent, center, max(2, self._s(4)))
        
        if bool(element.get("show_value_label", False)):
            self._draw_value_label(element, rect, value, y=rect.bottom - max(18, rect.height // 4))

    def _draw_value_sport_gauge(self, element: dict[str, Any], raw_value: Any, value: str) -> None:
        rect = self._rect(element)
        if rect.width <= 0 or rect.height <= 0:
            return
        ratio = self._value_ratio(raw_value, element)
        center = (rect.centerx, rect.centery + rect.height // 6)
        radius = max(8, min(rect.width // 2, int(rect.height * 0.62)))
        
        track_color = color_tuple(element.get("inactive_color", "#1a2430"), (26, 36, 48))
        redline = color_tuple(element.get("redline_color", "#ff3b30"), (255, 59, 48))
        needle_color = color_tuple(element.get("color", "#f6fbff"), (246, 251, 255))
        
        start = GAUGE_START_DEGREES
        sweep = GAUGE_SWEEP_DEGREES
        
        # 1. Thick Outer Track
        self._draw_aa_arc(self.screen, track_color, center, radius, math.radians(start), math.radians(start + sweep), max(2, self._s(4)))
        
        # 2. Redline inner arc (80% to 100%)
        self._draw_aa_arc(self.screen, redline, center, int(radius * 0.88), math.radians(start + sweep * 0.8), math.radians(start + sweep), max(2, self._s(4)))
        
        # Determine tick intervals
        min_val = self._numeric_value(element.get("min_value", 0)) or 0.0
        max_val = self._numeric_value(element.get("max_value", 100)) or 100.0
        range_val = max_val - min_val
        tick_interval = self._numeric_value(element.get("tick_interval"))
        
        # Auto calculate interval for sport gauge (aim for ~8 major ticks)
        if not tick_interval or tick_interval <= 0:
            magnitude = 10 ** math.floor(math.log10(max(1, range_val)))
            if range_val / magnitude < 3:
                tick_interval = magnitude / 5
            elif range_val / magnitude < 6:
                tick_interval = magnitude / 2
            else:
                tick_interval = magnitude
                
        num_major_ticks = max(1, int(range_val / tick_interval))
        sub_ticks = 4 # Minor ticks between major ones
        total_ticks = num_major_ticks * sub_ticks
        
        tick_font = self._font(int(element.get("font_size", 28)) // 2 + 2, element.get("font_family", "default"), "bold", "normal")
        
        # 3. Realistic Ticks (Major and Minor)
        for tick in range(0, total_ticks + 1):
            tick_ratio = tick / total_ticks
            angle = math.radians(start + sweep * tick_ratio)
            is_major = tick % sub_ticks == 0
            is_redline = tick_ratio >= 0.8
            
            tick_len = 0.12 if is_major else 0.05
            inner = (center[0] + int(math.cos(angle) * radius * (1.0 - tick_len)), center[1] + int(math.sin(angle) * radius * (1.0 - tick_len)))
            outer = (center[0] + int(math.cos(angle) * radius), center[1] + int(math.sin(angle) * radius))
            
            color = redline if is_redline else (needle_color if is_major else track_color)
            thickness = max(1, self._s(3 if is_major else 1))
            pygame.draw.line(self.screen, color, inner, outer, thickness)
            
            # Draw Labels for major ticks
            if is_major:
                tick_val = min_val + (tick / sub_ticks * tick_interval)
                # Display compact numbers for RPM (e.g. 1 instead of 1000) if range is high
                if range_val >= 1000 and tick_interval >= 500:
                   display_val = tick_val / 1000
                else:
                   display_val = tick_val
                   
                val_str = f"{int(display_val)}" if display_val.is_integer() else f"{display_val:.1f}"
                text_surf = tick_font.render(val_str, True, redline if is_redline else needle_color)
                
                text_ratio = 0.72
                text_pos = (center[0] + int(math.cos(angle) * radius * text_ratio), center[1] + int(math.sin(angle) * radius * text_ratio))
                self.screen.blit(text_surf, text_surf.get_rect(center=text_pos))
            
        # 4. Needle
        angle = math.radians(start + sweep * ratio)
        needle_len = radius * 0.95
        tail_len = radius * 0.20
        
        end = (center[0] + int(math.cos(angle) * needle_len), center[1] + int(math.sin(angle) * needle_len))
        tail = (center[0] - int(math.cos(angle) * tail_len), center[1] - int(math.sin(angle) * tail_len))
        
        # Needle shadow
        shadow_offset = max(1, self._s(3))
        pygame.draw.line(self.screen, (0, 0, 0, 150), (tail[0] + shadow_offset, tail[1] + shadow_offset), (end[0] + shadow_offset, end[1] + shadow_offset), max(2, self._s(6)))
        
        # Needle body
        pygame.draw.line(self.screen, redline, tail, end, max(2, self._s(4)))
        
        # Center Hub
        pygame.draw.circle(self.screen, (20, 25, 30), center, max(6, self._s(16)))
        pygame.draw.circle(self.screen, redline, center, max(4, self._s(12)), max(1, self._s(2)))
        
        if bool(element.get("show_value_label", False)):
            self._draw_value_label(element, rect, value, y=rect.centery - max(16, rect.height // 10))

    def _draw_aa_arc(self, surface: pygame.Surface, color: tuple[int, int, int], center: tuple[int, int], radius: int, start_angle: float, end_angle: float, width: int) -> None:
        if end_angle <= start_angle:
            return
        upscale = 2
        rect = pygame.Rect(0, 0, (radius + width) * 2 * upscale, (radius + width) * 2 * upscale)
        temp = pygame.Surface(rect.size, pygame.SRCALPHA)
        temp_center = (rect.width // 2, rect.height // 2)
        temp_rect = pygame.Rect(temp_center[0] - radius * upscale, temp_center[1] - radius * upscale, radius * 2 * upscale, radius * 2 * upscale)
        
        pygame.draw.arc(temp, color, temp_rect, start_angle, end_angle, width * upscale)
        
        scaled = pygame.transform.smoothscale(temp, (rect.width // upscale, rect.height // upscale))
        surface.blit(scaled, (center[0] - scaled.get_width() // 2, center[1] - scaled.get_height() // 2))

    def _draw_nav_icon(self, element: dict[str, Any], state: HudState) -> None:
        rect = self._rect(element)
        if rect.width <= 0 or rect.height <= 0:
            return
        event_type = self._int_from_state(state, element.get("event_binding", "nav.event_type"), 0)
        turn_side = self._int_from_state(state, element.get("side_binding", "nav.turn_side"), 3)
        color = color_tuple(element.get("color", "#f8fbff"), (248, 251, 255))
        accent = color_tuple(element.get("accent", "#1fd66f"), (31, 214, 111))
        inactive_color = color_tuple(element.get("inactive_color", "#53606a"), (83, 96, 106))
        active = bool(state.resolve("nav.connected", True))
        draw_color = color if active else inactive_color
        line_width = max(3, min(rect.width, rect.height) // 10)
        icon = self._load_nav_icon(self._nav_icon_name(event_type, turn_side))
        if icon is not None:
            scaled = pygame.transform.smoothscale(icon, (rect.width, rect.height))
            scaled = self._tint_alpha_surface(scaled, draw_color)
            self.screen.blit(scaled, rect)
            return

        if event_type in {15}:  # destination
            pygame.draw.circle(self.screen, draw_color, rect.center, max(6, min(rect.width, rect.height) // 5), width=line_width)
            pygame.draw.circle(self.screen, accent if active else inactive_color, rect.center, max(2, line_width // 2))
            return
        if event_type in {10, 11, 12}:  # roundabout variants
            radius = max(8, min(rect.width, rect.height) // 4)
            pygame.draw.circle(self.screen, draw_color, rect.center, radius, width=line_width)
            self._draw_lucide_arrow_head((rect.centerx + radius, rect.centery), "right", draw_color, line_width)
            return
        if event_type == 14:  # straight
            self._draw_lucide_straight_arrow(rect, draw_color, line_width)
            return
        if event_type == 6:  # U-turn
            self._draw_lucide_uturn(rect, draw_color, line_width)
            return

        direction = "right" if turn_side == 2 else "left" if turn_side == 1 else "up"
        if direction == "right":
            self._draw_lucide_corner_arrow(rect, "right", draw_color, line_width)
        elif direction == "left":
            self._draw_lucide_corner_arrow(rect, "left", draw_color, line_width)
        else:
            self._draw_lucide_straight_arrow(rect, draw_color, line_width)

    def _nav_icon_name(self, event_type: int, turn_side: int) -> str:
        if event_type == 15:
            return "flag"
        if event_type in {10, 11, 12}:
            return "roundabout_left" if turn_side == 1 else "roundabout_right"
        if event_type == 14:
            return "straight"
        if event_type == 6:
            return "u_turn_left" if turn_side == 1 else "u_turn_right"
        if turn_side == 2:
            return "turn_right"
        if turn_side == 1:
            return "turn_left"
        return "straight"

    def _lucide_point(self, rect: pygame.Rect, x: float, y: float) -> tuple[int, int]:
        inset = min(rect.width, rect.height) * 0.06
        width = max(1.0, rect.width - inset * 2)
        height = max(1.0, rect.height - inset * 2)
        return (int(rect.x + inset + width * x / 24), int(rect.y + inset + height * y / 24))

    def _draw_lucide_straight_arrow(self, rect: pygame.Rect, color: tuple[int, int, int], line_width: int) -> None:
        pygame.draw.line(self.screen, color, self._lucide_point(rect, 12, 19), self._lucide_point(rect, 12, 5), line_width)
        pygame.draw.line(self.screen, color, self._lucide_point(rect, 5, 12), self._lucide_point(rect, 12, 5), line_width)
        pygame.draw.line(self.screen, color, self._lucide_point(rect, 19, 12), self._lucide_point(rect, 12, 5), line_width)

    def _draw_lucide_corner_arrow(self, rect: pygame.Rect, direction: str, color: tuple[int, int, int], line_width: int) -> None:
        if direction == "left":
            points = [self._lucide_point(rect, 20, 20), self._lucide_point(rect, 20, 13), self._lucide_point(rect, 16, 9), self._lucide_point(rect, 4, 9)]
            arrow_tip = self._lucide_point(rect, 4, 9)
            arrow_a = self._lucide_point(rect, 9, 14)
            arrow_b = self._lucide_point(rect, 9, 4)
        else:
            points = [self._lucide_point(rect, 4, 20), self._lucide_point(rect, 4, 13), self._lucide_point(rect, 8, 9), self._lucide_point(rect, 20, 9)]
            arrow_tip = self._lucide_point(rect, 20, 9)
            arrow_a = self._lucide_point(rect, 15, 14)
            arrow_b = self._lucide_point(rect, 15, 4)
        pygame.draw.lines(self.screen, color, False, points, line_width)
        pygame.draw.line(self.screen, color, arrow_a, arrow_tip, line_width)
        pygame.draw.line(self.screen, color, arrow_b, arrow_tip, line_width)

    def _draw_lucide_uturn(self, rect: pygame.Rect, color: tuple[int, int, int], line_width: int) -> None:
        arc_rect = pygame.Rect(self._lucide_point(rect, 4, 4), (max(1, int(rect.width * 0.5)), max(1, int(rect.height * 0.5))))
        pygame.draw.line(self.screen, color, self._lucide_point(rect, 18, 20), self._lucide_point(rect, 18, 12), line_width)
        pygame.draw.arc(self.screen, color, arc_rect, math.radians(0), math.radians(180), line_width)
        self._draw_lucide_arrow_head(self._lucide_point(rect, 6, 12), "down", color, line_width)

    def _draw_lucide_arrow_head(self, point: tuple[int, int], direction: str, color: tuple[int, int, int], line_width: int) -> None:
        size = max(8, line_width * 2)
        x, y = point
        if direction == "right":
            pygame.draw.line(self.screen, color, (x - size, y - size), (x, y), line_width)
            pygame.draw.line(self.screen, color, (x - size, y + size), (x, y), line_width)
        elif direction == "down":
            pygame.draw.line(self.screen, color, (x - size, y - size), (x, y), line_width)
            pygame.draw.line(self.screen, color, (x + size, y - size), (x, y), line_width)
        else:
            pygame.draw.line(self.screen, color, (x + size, y - size), (x, y), line_width)
            pygame.draw.line(self.screen, color, (x + size, y + size), (x, y), line_width)

    def _draw_arrow_head(self, point: tuple[int, int], direction: str, color: tuple[int, int, int], line_width: int) -> None:
        size = max(8, line_width * 3)
        x, y = point
        if direction == "left":
            points = [(x, y), (x + size, y - size), (x + size, y + size)]
        elif direction == "right":
            points = [(x, y), (x - size, y - size), (x - size, y + size)]
        elif direction == "down":
            points = [(x, y), (x - size, y - size), (x + size, y - size)]
        else:
            points = [(x, y), (x - size, y + size), (x + size, y + size)]
        pygame.draw.polygon(self.screen, color, points)

    def _draw_gear_indicator(self, element: dict[str, Any], state: HudState) -> None:
        rect = self._rect(element)
        if rect.width <= 0 or rect.height <= 0:
            return
        binding = str(element.get("binding", "vehicle.gear_range"))
        active = str(state.resolve(binding, "--")).strip().upper()
        gears = element.get("gears", ["P", "R", "N", "D", "3", "2", "L"])
        if not isinstance(gears, list):
            gears = ["P", "R", "N", "D", "3", "2", "L"]
        normalized_gears = [str(gear).strip().upper() for gear in gears if str(gear).strip()]
        if not normalized_gears:
            normalized_gears = ["P", "R", "N", "D", "3", "2", "L"]
            
        style = str(element.get("gear_style", "strip"))
        active_color = color_tuple(element.get("active_color", element.get("accent", "#24d36b")), (36, 211, 107))
        inactive_color = color_tuple(element.get("inactive_color", "#4a5568"), (74, 85, 104))
        text_color = color_tuple(element.get("color", "#f6fbff"), (246, 251, 255))
        base_size = int(element.get("font_size", 28))
        active_size = int(element.get("active_font_size", max(base_size + 12, base_size * 2)))

        if style == "active_only":
            display = active if active and active != "--" else "--"
            font = self._font(active_size, element.get("font_family", "default"), "bold", element.get("font_style", "normal"), language=self.language)

            surface = font.render(display, True, active_color if display != "--" else inactive_color)
            self.screen.blit(surface, surface.get_rect(center=rect.center))
            return

        slot_width = max(1, rect.width // len(normalized_gears))
        for index, gear in enumerate(normalized_gears):
            slot = pygame.Rect(rect.x + slot_width * index, rect.y, slot_width, rect.height)
            is_active = gear == active

            font = self._font(
                active_size if is_active else base_size,
                element.get("font_family", "default"),
                "bold" if is_active else element.get("font_weight", "normal"),
                element.get("font_style", "normal"),
                language=self.language,
            )
            color = active_color if is_active else text_color
            surface = font.render(gear, True, color)
            self.screen.blit(surface, surface.get_rect(center=slot.center))

    def _int_from_state(self, state: HudState, binding: Any, fallback: int) -> int:
        try:
            return int(state.resolve(str(binding), fallback))
        except (TypeError, ValueError):
            return fallback

    def _draw_value_label(self, element: dict[str, Any], rect: pygame.Rect, value: str, y: int) -> None:
        text = f"{self._localized_element_text(element, 'prefix')}{value}{self._localized_element_text(element, 'suffix')}"
        label_rect = pygame.Rect(rect.x, y, rect.width, max(1, rect.height // 3))
        color = color_tuple(element.get("color", "#111111"))
        surface = self._fit_text_surface(text, element, label_rect, color)
        self.screen.blit(surface, surface.get_rect(center=label_rect.center))

    def _value_ratio(self, raw_value: Any, element: dict[str, Any]) -> float:
        numeric = self._numeric_value(raw_value)
        if numeric is None:
            return 0.0
        min_value = self._numeric_value(element.get("min_value", 0))
        max_value = self._numeric_value(element.get("max_value", 100))
        if min_value is None:
            min_value = 0.0
        if max_value is None or max_value <= min_value:
            max_value = min_value + 100.0
        return max(0.0, min(1.0, (numeric - min_value) / (max_value - min_value)))

    def _numeric_value(self, value: Any) -> float | None:
        if isinstance(value, bool) or value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _fit_text_surface(self, text: str, element: dict[str, Any], rect: pygame.Rect, color: tuple[int, int, int]) -> pygame.Surface:
        if rect.width <= 0 or rect.height <= 0:
            return pygame.Surface((0, 0), pygame.SRCALPHA)
        requested_size = int(element.get("font_size", 28))
        family = element.get("font_family", "default")
        weight = element.get("font_weight", "normal")
        style = element.get("font_style", "normal")
        min_size = 8
        for size in range(max(min_size, requested_size), min_size - 1, -1):
            surface = self._font(size, family, weight, style, language=self.language).render(text, True, color)
            if surface.get_width() <= rect.width and surface.get_height() <= rect.height:
                return surface
        return self._ellipsized_surface(text, min_size, family, weight, style, rect, color)

    def _ellipsized_surface(
        self,
        text: str,
        size: int,
        family: str,
        weight: str,
        style: str,
        rect: pygame.Rect,
        color: tuple[int, int, int],
    ) -> pygame.Surface:
        font = self._font(size, family, weight, style, language=self.language)
        if not text:
            return font.render("", True, color)
        ellipsis = "..."
        empty_surface = pygame.Surface((0, 0), pygame.SRCALPHA)
        ellipsis_surface = font.render(ellipsis, True, color)
        if ellipsis_surface.get_width() > rect.width or ellipsis_surface.get_height() > rect.height:
            return empty_surface
        for length in range(len(text), 0, -1):
            candidate = text[:length] + ellipsis
            surface = font.render(candidate, True, color)
            if surface.get_width() <= rect.width and surface.get_height() <= rect.height:
                return surface
        return empty_surface

    def _draw_warning_row(self, element: dict[str, Any], state: HudState) -> None:
        rect = self._rect(element)
        active_color = color_tuple(element.get("color", "#ff0000"))
        inactive_color = color_tuple(element.get("inactive_color", "#666666"))
        font = self._font(
            int(element.get("font_size", 22)),
            element.get("font_family", "default"),
            element.get("font_weight", "bold"),
            element.get("font_style", "normal"),
            language=self.language,
        )
        bindings = element.get("bindings", [])
        if not bindings:
            return
        step = max(1, rect.width // len(bindings))
        for index, binding in enumerate(bindings):
            active = bool(state.resolve(binding, False))
            label = WARNING_LABELS.get(self.language, WARNING_LABELS[DEFAULT_LANGUAGE]).get(binding, binding.split(".")[-1].upper())
            color = active_color if active else inactive_color
            lamp_rect = pygame.Rect(rect.x + step * index, rect.y, step - self._x(4), rect.height)
            text_surface = font.render(label, True, color)
            self.screen.blit(text_surface, text_surface.get_rect(center=lamp_rect.center))

    def _draw_warning_icon(self, element: dict[str, Any], state: HudState) -> None:
        binding = str(element.get("binding", "")).strip()
        active = bool(state.resolve(binding, False)) if binding else bool(element.get("show_when_inactive", False))
        if not active and not element.get("show_when_inactive", False):
            return
        icon = self._load_warning_icon(str(element.get("icon", element.get("id", ""))))
        if icon is None:
            return
        rect = self._rect(element)
        if rect.width <= 0 or rect.height <= 0:
            return
        scaled = pygame.transform.smoothscale(icon, (rect.width, rect.height))
        active_color_str = element.get("warning_color", WARNING_ACTIVE_COLORS.get(binding, "#ff3b30"))
        tint_color = color_tuple(active_color_str if active else element.get("inactive_color", "#4a5568"), (255, 59, 48) if active else (74, 85, 104))
        scaled = self._tint_alpha_surface(scaled, tint_color)

        alpha = int(element.get("inactive_alpha", 80)) if not active else 255
        if alpha != 255:
            scaled.set_alpha(alpha)
            
        self.screen.blit(scaled, rect)

    def _tint_alpha_surface(self, source: pygame.Surface, color: tuple[int, int, int]) -> pygame.Surface:
        tinted = pygame.Surface(source.get_size(), pygame.SRCALPHA)
        width, height = source.get_size()
        background = source.get_at((0, 0))
        opaque_pixels = 0
        foreground_pixels = 0
        use_background_key = background.a > 0
        if use_background_key:
            for y in range(height):
                for x in range(width):
                    pixel = source.get_at((x, y))
                    if not pixel.a:
                        continue
                    opaque_pixels += 1
                    if self._color_distance(pixel, background) > 18:
                        foreground_pixels += 1
            use_background_key = opaque_pixels > 0 and foreground_pixels / opaque_pixels > 0.02
        for y in range(height):
            for x in range(width):
                pixel = source.get_at((x, y))
                alpha = pixel.a
                if not alpha:
                    continue
                if use_background_key and self._color_distance(pixel, background) <= 18:
                    continue
                if alpha:
                    tinted.set_at((x, y), (color[0], color[1], color[2], alpha))
        return tinted

    def _color_distance(self, left: pygame.Color, right: pygame.Color) -> int:
        return abs(left.r - right.r) + abs(left.g - right.g) + abs(left.b - right.b)

    def _load_warning_icon(self, icon_name: str) -> pygame.Surface | None:
        clean = "".join(ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in icon_name.strip().lower())
        if not clean:
            return None
        if clean not in self.warning_icon_cache:
            path = WARNING_ICON_DIR / f"{clean}.png"
            if not path.exists():
                return None
            loaded = pygame.image.load(str(path))
            try:
                loaded = loaded.convert_alpha()
            except pygame.error:
                loaded = loaded.copy()
            self.warning_icon_cache[clean] = loaded
        return self.warning_icon_cache[clean]

    def _load_nav_icon(self, icon_name: str) -> pygame.Surface | None:
        clean = "".join(ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in icon_name.strip().lower())
        if not clean:
            return None
        if clean not in self.nav_icon_cache:
            path = NAV_ICON_DIR / f"{clean}.png"
            if not path.exists():
                return None
            loaded = pygame.image.load(str(path))
            try:
                loaded = loaded.convert_alpha()
            except pygame.error:
                loaded = loaded.copy()
            self.nav_icon_cache[clean] = loaded
        return self.nav_icon_cache[clean]

    def _x(self, value: float | int) -> int:
        return int(float(value) * self.scale_x)

    def _y(self, value: float | int) -> int:
        return int(float(value) * self.scale_y)

    def _s(self, value: float | int) -> int:
        return max(1, int(float(value) * min(self.scale_x, self.scale_y)))

    def _localized_element_text(self, element: dict[str, Any], key: str, fallback: Any = "") -> str:
        translations = element.get(f"{key}_i18n")
        if isinstance(translations, dict):
            translated = translations.get(self.language)
            if translated is None:
                translated = translations.get(DEFAULT_LANGUAGE)
            if translated is not None:
                return str(translated)
        return str(element.get(key, fallback))
