from __future__ import annotations

import base64
import math
import os
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from hud_pi.renderer import MATERIAL_NAV_ICON_SOURCE, HudRenderer, format_value
from hud_pi.state import HudState


class RecordingScreen:
    def __init__(self, width: int = 1920, height: int = 480) -> None:
        self.width = width
        self.height = height
        self.blits: list[tuple[pygame.Surface, pygame.Rect]] = []

    def get_width(self) -> int:
        return self.width

    def get_height(self) -> int:
        return self.height

    def fill(self, _color: tuple[int, int, int]) -> None:
        return None

    def blit(self, surface: pygame.Surface, target: pygame.Rect) -> None:
        self.blits.append((surface, target.copy()))


class WideFakeFont:
    def __init__(self, size: int) -> None:
        self.size = size

    def render(self, text: str, _antialias: bool, _color: tuple[int, int, int]) -> pygame.Surface:
        return pygame.Surface((max(1, len(text) * self.size), max(1, self.size)))


class RecordingFont:
    def __init__(self) -> None:
        self.rendered_texts: list[str] = []

    def render(self, text: str, _antialias: bool, _color: tuple[int, int, int]) -> pygame.Surface:
        self.rendered_texts.append(text)
        return pygame.Surface((max(1, len(text) * 8), 16))


class RendererFormattingTest(unittest.TestCase):
    def test_format_value_uses_on_off_for_booleans(self) -> None:
        self.assertEqual("ON", format_value(True))
        self.assertEqual("OFF", format_value(False))

    def test_format_value_joins_list_values_for_dtc_display(self) -> None:
        self.assertEqual("P0133, U0100", format_value(["P0133", "U0100"]))

    def test_format_value_marks_empty_list_as_none(self) -> None:
        self.assertEqual("NONE", format_value([]))

    def test_format_value_supports_korean_status_words(self) -> None:
        self.assertEqual("켜짐", format_value(True, language="ko"))
        self.assertEqual("꺼짐", format_value(False, language="ko"))
        self.assertEqual("없음", format_value([], language="ko"))

    def test_font_uses_element_family_weight_and_style(self) -> None:
        renderer = object.__new__(HudRenderer)
        renderer.font_cache = {}
        renderer.scale_x = 1
        renderer.scale_y = 1

        with patch("hud_pi.renderer.pygame.font.SysFont", return_value=Mock()) as sys_font:
            renderer._font(24, family="Verdana", weight="bold", style="italic")

        sys_font.assert_called_once_with("Verdana", 24, bold=True, italic=True)

    def test_default_font_uses_pygame_builtin_font_for_cross_platform_rendering(self) -> None:
        renderer = object.__new__(HudRenderer)
        renderer.font_cache = {}
        renderer.scale_x = 1
        renderer.scale_y = 1
        font = Mock()

        with patch("hud_pi.renderer.pygame.font.Font", return_value=font) as builtin_font, patch(
            "hud_pi.renderer.pygame.font.SysFont"
        ) as sys_font:
            renderer._font(24, family="default", weight="bold", style="italic")

        builtin_font.assert_called_once_with(None, 24)
        font.set_bold.assert_called_once_with(True)
        font.set_italic.assert_called_once_with(True)
        sys_font.assert_not_called()

    def test_korean_default_font_uses_cjk_system_font_candidates(self) -> None:
        renderer = object.__new__(HudRenderer)
        renderer.font_cache = {}
        renderer.scale_x = 1
        renderer.scale_y = 1

        with patch("hud_pi.renderer.pygame.font.SysFont", return_value=Mock()) as sys_font, patch(
            "hud_pi.renderer.pygame.font.Font"
        ) as builtin_font:
            renderer._font(24, family="default", weight="normal", style="normal", language="ko")

        sys_font.assert_called_once()
        font_names = sys_font.call_args.args[0]
        self.assertIn("Noto Sans CJK KR", font_names)
        builtin_font.assert_not_called()

    def test_text_element_uses_layout_language_translation(self) -> None:
        screen = pygame.Surface((420, 96))
        layout = {"language": "ko", "canvas": {"width": 1920, "height": 480, "background": "#000000"}, "elements": []}
        renderer = HudRenderer(layout, screen)  # type: ignore[arg-type]
        element = {
            "id": "status",
            "type": "text",
            "text": "READY",
            "text_i18n": {"ko": "준비", "en": "READY"},
            "x": 10,
            "y": 20,
            "w": 160,
            "h": 40,
            "font_size": 24,
            "font_family": "default",
            "font_weight": "normal",
            "font_style": "normal",
            "color": "#ffffff",
            "align": "left",
        }
        captured: list[str] = []

        def fit_text(text: str, *_args: object) -> pygame.Surface:
            captured.append(text)
            return pygame.Surface((40, 16))

        with patch.object(renderer, "_fit_text_surface", side_effect=fit_text):
            renderer._draw_textual(element, HudState({}))

        self.assertEqual(["준비"], captured)

    def test_value_ratio_uses_element_min_and_max_values(self) -> None:
        screen = pygame.Surface((420, 96))
        layout = {"canvas": {"width": 420, "height": 96, "background": "#000000"}, "elements": []}
        renderer = HudRenderer(layout, screen)

        self.assertEqual(0.5, renderer._value_ratio(4000, {"min_value": 0, "max_value": 8000}))
        self.assertEqual(0.0, renderer._value_ratio(-100, {"min_value": 0, "max_value": 8000}))
        self.assertEqual(1.0, renderer._value_ratio(9000, {"min_value": 0, "max_value": 8000}))

    def test_value_bar_style_uses_bar_renderer(self) -> None:
        screen = RecordingScreen()
        layout = {"canvas": {"width": 1920, "height": 480, "background": "#000000"}, "elements": []}
        renderer = HudRenderer(layout, screen)  # type: ignore[arg-type]
        element = {
            "id": "speed_bar",
            "type": "value",
            "value_style": "bar",
            "binding": "vehicle.speed_kmh",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 60,
            "max_value": 220,
        }

        with patch.object(renderer, "_draw_value_bar") as draw_bar:
            renderer._draw_textual(element, HudState({"vehicle": {"speed_kmh": 110}}))

        draw_bar.assert_called_once()

    def test_value_bar_draws_segment_separators_for_cluster_style(self) -> None:
        screen = pygame.Surface((360, 100))
        layout = {"canvas": {"width": 360, "height": 100, "background": "#000000"}, "elements": []}
        renderer = HudRenderer(layout, screen)
        element = {
            "id": "fuel_bar",
            "type": "value",
            "value_style": "bar",
            "binding": "vehicle.fuel_percent",
            "x": 20,
            "y": 20,
            "w": 300,
            "h": 60,
            "min_value": 0,
            "max_value": 100,
            "font_size": 18,
            "font_family": "default",
            "font_weight": "normal",
            "font_style": "normal",
            "color": "#ffffff",
            "accent": "#20d46b",
            "inactive_color": "#2d3740",
        }

        with patch.object(renderer, "_draw_value_label") as draw_label, patch("hud_pi.renderer.pygame.draw.line", wraps=pygame.draw.line) as draw_line:
            renderer._draw_value_bar(element, 72, "72")

        self.assertGreaterEqual(draw_line.call_count, 6)
        draw_label.assert_not_called()

    def test_value_bar_draws_label_only_when_explicitly_enabled(self) -> None:
        screen = pygame.Surface((360, 100))
        layout = {"canvas": {"width": 360, "height": 100, "background": "#000000"}, "elements": []}
        renderer = HudRenderer(layout, screen)
        element = {
            "id": "fuel_bar",
            "type": "value",
            "value_style": "bar",
            "binding": "vehicle.fuel_percent",
            "x": 20,
            "y": 20,
            "w": 300,
            "h": 60,
            "min_value": 0,
            "max_value": 100,
            "show_value_label": True,
        }

        with patch.object(renderer, "_draw_value_label") as draw_label:
            renderer._draw_value_bar(element, 72, "72")

        draw_label.assert_called_once()

    def test_textual_elements_do_not_draw_background_panels_or_left_rules(self) -> None:
        screen = pygame.Surface((240, 80))
        layout = {"canvas": {"width": 240, "height": 80, "background": "#000000"}, "elements": []}
        renderer = HudRenderer(layout, screen)
        element = {
            "id": "voltage",
            "type": "value",
            "binding": "vehicle.voltage_v",
            "x": 20,
            "y": 20,
            "w": 160,
            "h": 40,
            "font_size": 24,
            "font_family": "default",
            "font_weight": "normal",
            "font_style": "normal",
            "color": "#ffffff",
        }

        with patch.object(renderer, "_fit_text_surface", return_value=pygame.Surface((40, 16))), patch(
            "hud_pi.renderer.pygame.draw.rect", wraps=pygame.draw.rect
        ) as draw_rect:
            renderer._draw_textual(element, HudState({"vehicle": {"voltage_v": 14.1}}))

        draw_rect.assert_not_called()

    def test_value_bar_does_not_draw_an_element_background_panel(self) -> None:
        screen = pygame.Surface((360, 100))
        layout = {"canvas": {"width": 360, "height": 100, "background": "#000000"}, "elements": []}
        renderer = HudRenderer(layout, screen)
        element = {
            "id": "fuel_bar",
            "type": "value",
            "value_style": "bar",
            "binding": "vehicle.fuel_percent",
            "x": 20,
            "y": 20,
            "w": 300,
            "h": 60,
            "min_value": 0,
            "max_value": 100,
            "font_size": 18,
            "font_family": "default",
            "font_weight": "normal",
            "font_style": "normal",
            "color": "#ffffff",
            "accent": "#20d46b",
            "inactive_color": "#2d3740",
        }
        element_rect = pygame.Rect(20, 20, 300, 60)

        with patch.object(renderer, "_draw_value_label"), patch("hud_pi.renderer.pygame.draw.rect", wraps=pygame.draw.rect) as draw_rect:
            renderer._draw_value_bar(element, 72, "72")

        full_panel_calls = [
            call
            for call in draw_rect.call_args_list
            if len(call.args) >= 3 and isinstance(call.args[2], pygame.Rect) and call.args[2] == element_rect
        ]
        self.assertEqual([], full_panel_calls)

    def test_gauge_arcs_leave_bottom_gap_between_five_and_seven_oclock(self) -> None:
        screen = pygame.Surface((420, 240))
        layout = {"canvas": {"width": 420, "height": 240, "background": "#000000"}, "elements": []}
        renderer = HudRenderer(layout, screen)
        element = {
            "id": "gauge",
            "type": "value",
            "binding": "vehicle.speed_kmh",
            "x": 20,
            "y": 20,
            "w": 360,
            "h": 180,
            "min_value": 0,
            "max_value": 220,
            "font_size": 22,
            "font_family": "default",
            "font_weight": "normal",
            "font_style": "normal",
            "color": "#ffffff",
            "accent": "#20d46b",
            "inactive_color": "#2d3740",
        }
        expected_start = math.radians(135)
        expected_end = math.radians(405)

        for draw_method in (renderer._draw_value_analog, renderer._draw_value_needle, renderer._draw_value_sport_gauge):
            with self.subTest(draw_method=draw_method.__name__):
                with patch.object(renderer, "_draw_value_label") as draw_label, patch("hud_pi.renderer.pygame.draw.arc", wraps=pygame.draw.arc) as draw_arc:
                    draw_method(element, 110, "110")
                self.assertGreaterEqual(draw_arc.call_count, 1)
                draw_label.assert_not_called()
                track_call = draw_arc.call_args_list[0]
                self.assertAlmostEqual(expected_start, track_call.args[3], delta=0.01)
                self.assertAlmostEqual(expected_end, track_call.args[4], delta=0.01)

    def test_value_needle_style_uses_needle_renderer(self) -> None:
        screen = RecordingScreen()
        layout = {"canvas": {"width": 1920, "height": 480, "background": "#000000"}, "elements": []}
        renderer = HudRenderer(layout, screen)  # type: ignore[arg-type]
        element = {
            "id": "speed_needle",
            "type": "value",
            "value_style": "needle",
            "binding": "vehicle.speed_kmh",
            "x": 0,
            "y": 0,
            "w": 260,
            "h": 180,
            "max_value": 220,
        }

        with patch.object(renderer, "_draw_value_needle") as draw_needle:
            renderer._draw_textual(element, HudState({"vehicle": {"speed_kmh": 80}}))

        draw_needle.assert_called_once()

    def test_value_analog_style_uses_analog_renderer(self) -> None:
        screen = RecordingScreen()
        layout = {"canvas": {"width": 1920, "height": 480, "background": "#000000"}, "elements": []}
        renderer = HudRenderer(layout, screen)  # type: ignore[arg-type]
        element = {
            "id": "speed_analog",
            "type": "value",
            "value_style": "analog",
            "binding": "vehicle.speed_kmh",
            "x": 0,
            "y": 0,
            "w": 260,
            "h": 180,
            "max_value": 220,
        }

        with patch.object(renderer, "_draw_value_analog") as draw_analog:
            renderer._draw_textual(element, HudState({"vehicle": {"speed_kmh": 80}}))

        draw_analog.assert_called_once()

    def test_value_sport_gauge_style_uses_sport_renderer(self) -> None:
        screen = RecordingScreen()
        layout = {"canvas": {"width": 1920, "height": 480, "background": "#000000"}, "elements": []}
        renderer = HudRenderer(layout, screen)  # type: ignore[arg-type]
        element = {
            "id": "rpm_gauge",
            "type": "value",
            "value_style": "sport_gauge",
            "binding": "vehicle.rpm",
            "x": 0,
            "y": 0,
            "w": 360,
            "h": 220,
            "max_value": 8000,
        }

        with patch.object(renderer, "_draw_value_sport_gauge") as draw_sport:
            renderer._draw_textual(element, HudState({"vehicle": {"rpm": 4200}}))

        draw_sport.assert_called_once()

    def test_nav_icon_element_uses_navigation_icon_renderer(self) -> None:
        screen = RecordingScreen()
        layout = {"canvas": {"width": 1920, "height": 480, "background": "#000000"}, "elements": []}
        renderer = HudRenderer(layout, screen)  # type: ignore[arg-type]
        element = {
            "id": "nav_icon",
            "type": "nav_icon",
            "x": 0,
            "y": 0,
            "w": 96,
            "h": 96,
        }

        with patch.object(renderer, "_draw_nav_icon") as draw_nav_icon:
            renderer._render_elements([element], HudState({"nav": {"event_type": 4, "turn_side": 2}}))

        draw_nav_icon.assert_called_once()

    def test_gear_indicator_element_uses_dedicated_renderer(self) -> None:
        screen = RecordingScreen()
        layout = {"canvas": {"width": 1920, "height": 480, "background": "#000000"}, "elements": []}
        renderer = HudRenderer(layout, screen)  # type: ignore[arg-type]
        element = {
            "id": "gear_range",
            "type": "gear_indicator",
            "binding": "vehicle.gear_range",
            "x": 0,
            "y": 0,
            "w": 320,
            "h": 96,
            "gears": ["P", "R", "N", "D", "3", "2", "L"],
            "gear_style": "strip",
        }

        with patch.object(renderer, "_draw_gear_indicator") as draw_gear:
            renderer._render_elements([element], HudState({"vehicle": {"gear_range": "D"}}))

        draw_gear.assert_called_once()

    def test_gear_indicator_strip_draws_all_gears_with_active_gear_largest(self) -> None:
        screen = pygame.Surface((420, 96))
        layout = {"canvas": {"width": 420, "height": 96, "background": "#000000"}, "elements": []}
        renderer = HudRenderer(layout, screen)
        rendered: list[tuple[str, int]] = []

        class GearFont:
            def __init__(self, size: int) -> None:
                self.size = size

            def render(self, text: str, _antialias: bool, _color: tuple[int, int, int]) -> pygame.Surface:
                rendered.append((text, self.size))
                return pygame.Surface((max(1, len(text) * self.size), self.size))

        element = {
            "id": "gear_range",
            "type": "gear_indicator",
            "binding": "vehicle.gear_range",
            "x": 0,
            "y": 0,
            "w": 420,
            "h": 96,
            "font_size": 28,
            "active_font_size": 72,
            "gears": ["P", "R", "N", "D", "3", "2", "L"],
            "gear_style": "strip",
        }

        with patch.object(renderer, "_font", side_effect=lambda size, *_args, **_kwargs: GearFont(size)):
            renderer._draw_gear_indicator(element, HudState({"vehicle": {"gear_range": "D"}}))

        self.assertEqual(["P", "R", "N", "D", "3", "2", "L"], [text for text, _size in rendered])
        active_size = next(size for text, size in rendered if text == "D")
        inactive_sizes = [size for text, size in rendered if text != "D"]
        self.assertTrue(all(active_size > size for size in inactive_sizes))

    def test_nav_icon_draws_nonblank_maneuver_symbol_from_numeric_fields(self) -> None:
        screen = pygame.Surface((160, 160))
        layout = {"canvas": {"width": 160, "height": 160, "background": "#000000"}, "elements": []}
        renderer = HudRenderer(layout, screen)
        element = {
            "id": "nav_icon",
            "type": "nav_icon",
            "x": 20,
            "y": 20,
            "w": 120,
            "h": 120,
            "color": "#ffffff",
            "accent": "#20d46b",
        }
        background = screen.get_at((0, 0))

        renderer._draw_nav_icon(element, HudState({"nav": {"event_type": 4, "turn_side": 2}}))

        changed_pixels = 0
        for x in range(screen.get_width()):
            for y in range(screen.get_height()):
                if screen.get_at((x, y)) != background:
                    changed_pixels += 1
        self.assertGreater(changed_pixels, 200)

    def test_material_navigation_icon_assets_are_available(self) -> None:
        icon_dir = Path("pi-hud/assets/nav-icons")
        for icon_name in ["turn_left", "turn_right", "u_turn_left", "u_turn_right", "straight", "roundabout_left", "roundabout_right", "flag"]:
            path = icon_dir / f"{icon_name}.png"
            self.assertTrue(path.exists(), icon_name)
            surface = pygame.image.load(str(path))
            self.assertNotEqual(0, surface.get_masks()[3], icon_name)

    def test_nav_icon_uses_material_source_and_no_container_background(self) -> None:
        screen = pygame.Surface((160, 160))
        layout = {"canvas": {"width": 160, "height": 160, "background": "#000000"}, "elements": []}
        renderer = HudRenderer(layout, screen)
        element = {
            "id": "nav_icon",
            "type": "nav_icon",
            "x": 20,
            "y": 20,
            "w": 120,
            "h": 120,
            "color": "#ffffff",
            "accent": "#20d46b",
        }

        with patch("hud_pi.renderer.pygame.draw.rect", wraps=pygame.draw.rect) as draw_rect:
            renderer._draw_nav_icon(element, HudState({"nav": {"event_type": 4, "turn_side": 2, "connected": True}}))

        self.assertIn("@material-design-icons/svg", MATERIAL_NAV_ICON_SOURCE)
        draw_rect.assert_not_called()

    def test_gear_strip_active_gear_has_no_background_or_border(self) -> None:
        screen = pygame.Surface((420, 96))
        layout = {"canvas": {"width": 420, "height": 96, "background": "#000000"}, "elements": []}
        renderer = HudRenderer(layout, screen)

        class GearFont:
            def render(self, _text: str, _antialias: bool, _color: tuple[int, int, int]) -> pygame.Surface:
                return pygame.Surface((20, 20))

        element = {
            "id": "gear_range",
            "type": "gear_indicator",
            "binding": "vehicle.gear_range",
            "x": 0,
            "y": 0,
            "w": 420,
            "h": 96,
            "font_size": 28,
            "active_font_size": 72,
            "gears": ["P", "R", "N", "D", "3", "2", "L"],
            "gear_style": "strip",
        }

        with patch.object(renderer, "_font", return_value=GearFont()), patch("hud_pi.renderer.pygame.draw.rect", wraps=pygame.draw.rect) as draw_rect:
            renderer._draw_gear_indicator(element, HudState({"vehicle": {"gear_range": "D"}}))

        draw_rect.assert_not_called()

    def test_gear_active_only_has_no_background(self) -> None:
        screen = pygame.Surface((180, 110))
        layout = {"canvas": {"width": 180, "height": 110, "background": "#000000"}, "elements": []}
        renderer = HudRenderer(layout, screen)

        class GearFont:
            def render(self, _text: str, _antialias: bool, _color: tuple[int, int, int]) -> pygame.Surface:
                return pygame.Surface((20, 20))

        element = {
            "id": "gear_active",
            "type": "gear_indicator",
            "binding": "vehicle.gear_range",
            "x": 0,
            "y": 0,
            "w": 180,
            "h": 110,
            "font_size": 48,
            "active_font_size": 92,
            "gear_style": "active_only",
        }

        with patch.object(renderer, "_font", return_value=GearFont()), patch("hud_pi.renderer.pygame.draw.rect", wraps=pygame.draw.rect) as draw_rect:
            renderer._draw_gear_indicator(element, HudState({"vehicle": {"gear_range": "D"}}))

        draw_rect.assert_not_called()

    def test_renderer_draws_embedded_background_image_before_elements(self) -> None:
        png_bytes = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQImWP4z8AAAAMBAQCc479ZAAAAAElFTkSuQmCC")
        screen = pygame.Surface((8, 8))
        layout = {
            "canvas": {
                "width": 8,
                "height": 8,
                "background": "#000000",
                "background_image": "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii"),
                "background_image_fit": "stretch",
            },
            "elements": [],
        }
        renderer = HudRenderer(layout, screen)

        renderer.render(HudState({}))

        self.assertEqual((255, 0, 0), screen.get_at((4, 4))[:3])

    def test_warning_row_uses_korean_labels_when_layout_language_is_korean(self) -> None:
        screen = pygame.Surface((1920, 480))
        layout = {"language": "ko", "canvas": {"width": 1920, "height": 480, "background": "#000000"}, "elements": []}
        renderer = HudRenderer(layout, screen)
        font = RecordingFont()
        element = {
            "id": "warnings",
            "type": "warning_row",
            "bindings": ["warnings.door_open", "warnings.check_engine", "warnings.coolant_temp"],
            "x": 0,
            "y": 0,
            "w": 360,
            "h": 40,
            "font_size": 16,
            "font_family": "default",
            "font_weight": "bold",
            "font_style": "normal",
            "color": "#ff0000",
            "inactive_color": "#888888",
        }

        with patch.object(renderer, "_font", return_value=font):
            renderer._draw_warning_row(element, HudState({"warnings": {}}))

        self.assertEqual(["도어", "엔진", "수온"], font.rendered_texts)

    def test_warning_row_does_not_draw_background_cards(self) -> None:
        screen = pygame.Surface((360, 48))
        layout = {"language": "ko", "canvas": {"width": 360, "height": 48, "background": "#000000"}, "elements": []}
        renderer = HudRenderer(layout, screen)
        element = {
            "id": "warnings",
            "type": "warning_row",
            "bindings": ["warnings.door_open", "warnings.check_engine"],
            "x": 0,
            "y": 0,
            "w": 360,
            "h": 48,
            "font_size": 16,
            "font_family": "default",
            "font_weight": "bold",
            "font_style": "normal",
            "color": "#ff0000",
            "inactive_color": "#888888",
        }

        with patch.object(renderer, "_font", return_value=RecordingFont()), patch("hud_pi.renderer.pygame.draw.rect", wraps=pygame.draw.rect) as draw_rect:
            renderer._draw_warning_row(element, HudState({"warnings": {"door_open": True}}))

        draw_rect.assert_not_called()

    def test_textual_element_shrinks_text_to_fit_element_bounds(self) -> None:
        screen = RecordingScreen()
        layout = {"canvas": {"width": 1920, "height": 480, "background": "#000000"}, "elements": []}
        renderer = HudRenderer(layout, screen)  # type: ignore[arg-type]
        element = {
            "id": "nav_instruction",
            "type": "value",
            "binding": "nav.instruction",
            "x": 10,
            "y": 20,
            "w": 120,
            "h": 28,
            "font_size": 48,
            "font_family": "Arial",
            "font_weight": "normal",
            "font_style": "normal",
            "color": "#ffffff",
            "align": "left",
        }
        state = HudState({"nav": {"instruction": "very long navigation instruction"}})

        with patch.object(renderer, "_font", side_effect=lambda size, *_args, **_kwargs: WideFakeFont(size)):
            renderer._draw_textual(element, state)

        surface, target = screen.blits[-1]
        rect = renderer._rect(element)
        self.assertLessEqual(surface.get_width(), rect.width)
        self.assertLessEqual(surface.get_height(), rect.height)
        self.assertGreaterEqual(target.left, rect.left)
        self.assertLessEqual(target.right, rect.right)

    def test_textual_element_uses_empty_surface_when_element_is_too_small_for_text(self) -> None:
        screen = RecordingScreen()
        layout = {"canvas": {"width": 1920, "height": 480, "background": "#000000"}, "elements": []}
        renderer = HudRenderer(layout, screen)  # type: ignore[arg-type]
        element = {
            "id": "tiny_label",
            "type": "text",
            "text": "tiny",
            "x": 10,
            "y": 20,
            "w": 4,
            "h": 4,
            "font_size": 48,
            "font_family": "Arial",
            "font_weight": "normal",
            "font_style": "normal",
            "color": "#ffffff",
            "align": "left",
        }

        with patch.object(renderer, "_font", side_effect=lambda size, *_args, **_kwargs: WideFakeFont(size)):
            renderer._draw_textual(element, HudState({}))

        surface, target = screen.blits[-1]
        rect = renderer._rect(element)
        self.assertLessEqual(surface.get_width(), rect.width)
        self.assertLessEqual(surface.get_height(), rect.height)
        self.assertGreaterEqual(target.left, rect.left)
        self.assertLessEqual(target.right, rect.right)


if __name__ == "__main__":
    unittest.main()
