from __future__ import annotations

import math
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from hud_pi import pygame_gauge
from hud_pi.gauge_geometry import (
    GaugeTickEntry,
    SportGaugeTickEntry,
    analog_gauge_geometry,
    gauge_point,
    gauge_tick_entries,
    needle_gauge_geometry,
    sport_gauge_geometry,
    sport_gauge_needle_shape,
    sport_gauge_tick_entries,
)
from hud_pi.pygame_gauge import (
    draw_gauge_pointer,
    draw_gauge_progress_arcs,
    draw_gauge_ticks,
    draw_sport_gauge_arcs,
    draw_sport_gauge_pointer,
    draw_sport_gauge_ticks,
)


class RecordingTarget:
    def __init__(self) -> None:
        self.blits: list[tuple[pygame.Surface, pygame.Rect]] = []

    def blit(self, surface: pygame.Surface, target: pygame.Rect) -> None:
        self.blits.append((surface, target.copy()))


class RecordingFont:
    def __init__(self) -> None:
        self.rendered: list[tuple[str, tuple[int, int, int]]] = []

    def render(self, text: str, _antialias: bool, color: tuple[int, int, int]) -> pygame.Surface:
        self.rendered.append((text, color))
        return pygame.Surface((10, 6))


class PygameGaugeTest(unittest.TestCase):
    def test_draw_sport_gauge_element_prepares_redline_ticks_and_pointer(self) -> None:
        target = RecordingTarget()
        font = RecordingFont()
        element = {
            "inactive_color": "#102030",
            "redline_color": "#405060",
            "color": "#708090",
            "font_size": 28,
            "font_family": "mono",
            "min_value": 0,
            "max_value": 8000,
        }
        font_requests: list[tuple[int, str, str, str]] = []

        def font_factory(size: int, family: str, weight: str, style: str) -> RecordingFont:
            font_requests.append((size, family, weight, style))
            return font

        scale_size = lambda value: int(value * 2)
        self.assertTrue(hasattr(pygame_gauge, "draw_sport_gauge_element"))
        with patch("hud_pi.pygame_sport_gauge.draw_sport_gauge_arcs") as draw_arcs, patch(
            "hud_pi.pygame_sport_gauge.draw_sport_gauge_ticks"
        ) as draw_ticks, patch("hud_pi.pygame_sport_gauge.draw_sport_gauge_pointer") as draw_pointer:
            pygame_gauge.draw_sport_gauge_element(
                target,  # type: ignore[arg-type]
                element,
                rect=(10, 20, 200, 100),
                ratio=0.5,
                font_factory=font_factory,
                scale_size=scale_size,
            )

        center, radius = sport_gauge_geometry((10, 20, 200, 100))
        self.assertEqual(
            {
                "center": center,
                "radius": radius,
                "track_color": (16, 32, 48),
                "redline_color": (64, 80, 96),
                "scale_width": scale_size,
            },
            draw_arcs.call_args.kwargs,
        )
        self.assertEqual((target, sport_gauge_tick_entries(element, center=center, radius=radius)), draw_ticks.call_args.args)
        self.assertEqual(
            {
                "redline_color": (64, 80, 96),
                "major_color": (112, 128, 144),
                "minor_color": (16, 32, 48),
                "font": font,
                "scale_width": scale_size,
            },
            draw_ticks.call_args.kwargs,
        )
        end, tail = sport_gauge_needle_shape(center=center, radius=radius, ratio=0.5)
        self.assertEqual(
            {
                "center": center,
                "end": end,
                "tail": tail,
                "redline_color": (64, 80, 96),
                "scale_width": scale_size,
            },
            draw_pointer.call_args.kwargs,
        )
        self.assertEqual([(16, "mono", "bold", "normal")], font_requests)

    def test_draw_analog_gauge_element_prepares_colors_geometry_and_ticks(self) -> None:
        target = RecordingTarget()
        font = RecordingFont()
        element = {
            "inactive_color": "#102030",
            "accent": "#405060",
            "color": "#708090",
            "font_size": 32,
            "font_family": "mono",
            "min_value": 0,
            "max_value": 220,
        }
        font_requests: list[tuple[int, str, str, str]] = []

        def font_factory(size: int, family: str, weight: str, style: str) -> RecordingFont:
            font_requests.append((size, family, weight, style))
            return font

        scale_size = lambda value: int(value * 2)
        self.assertTrue(hasattr(pygame_gauge, "draw_analog_gauge_element"))
        with patch("hud_pi.pygame_standard_gauge.draw_gauge_progress_arcs") as draw_arcs, patch(
            "hud_pi.pygame_standard_gauge.draw_gauge_ticks"
        ) as draw_ticks:
            pygame_gauge.draw_analog_gauge_element(
                target,  # type: ignore[arg-type]
                element,
                rect=(10, 20, 200, 100),
                ratio=0.5,
                font_factory=font_factory,
                scale_size=scale_size,
            )

        center, radius = analog_gauge_geometry((10, 20, 200, 100))
        self.assertEqual(
            {
                "center": center,
                "radius": radius,
                "ratio": 0.5,
                "track_color": (16, 32, 48),
                "progress_color": (64, 80, 96),
                "width": 16,
            },
            draw_arcs.call_args.kwargs,
        )
        self.assertEqual(
            (
                target,
                gauge_tick_entries(
                    element,
                    center=center,
                    radius=radius,
                    outer_ratio=1.0,
                    major_inner_ratio=0.82,
                    minor_inner_ratio=0.90,
                    label_ratio=0.70,
                ),
            ),
            draw_ticks.call_args.args,
        )
        self.assertEqual({"color": (112, 128, 144), "font": font, "scale_width": scale_size}, draw_ticks.call_args.kwargs)
        self.assertEqual([(16, "mono", "normal", "normal")], font_requests)

    def test_draw_needle_gauge_element_prepares_colors_geometry_ticks_and_pointer(self) -> None:
        target = RecordingTarget()
        font = RecordingFont()
        element = {
            "inactive_color": "#102030",
            "accent": "#405060",
            "color": "#708090",
            "font_size": 28,
            "font_family": "mono",
            "min_value": 0,
            "max_value": 220,
        }
        font_requests: list[tuple[int, str, str, str]] = []

        def font_factory(size: int, family: str, weight: str, style: str) -> RecordingFont:
            font_requests.append((size, family, weight, style))
            return font

        scale_size = lambda value: int(value * 2)
        self.assertTrue(hasattr(pygame_gauge, "draw_needle_gauge_element"))
        with patch("hud_pi.pygame_standard_gauge.draw_gauge_progress_arcs") as draw_arcs, patch(
            "hud_pi.pygame_standard_gauge.draw_gauge_ticks"
        ) as draw_ticks, patch("hud_pi.pygame_standard_gauge.draw_gauge_pointer") as draw_pointer:
            pygame_gauge.draw_needle_gauge_element(
                target,  # type: ignore[arg-type]
                element,
                rect=(10, 20, 200, 100),
                ratio=0.5,
                font_factory=font_factory,
                scale_size=scale_size,
            )

        center, radius = needle_gauge_geometry((10, 20, 200, 100))
        self.assertEqual(
            {
                "center": center,
                "radius": radius,
                "ratio": 0.5,
                "track_color": (16, 32, 48),
                "progress_color": (64, 80, 96),
                "width": 12,
            },
            draw_arcs.call_args.kwargs,
        )
        self.assertEqual(
            (
                target,
                gauge_tick_entries(
                    element,
                    center=center,
                    radius=radius,
                    outer_ratio=0.96,
                    major_inner_ratio=0.84,
                    minor_inner_ratio=0.88,
                    label_ratio=0.72,
                ),
            ),
            draw_ticks.call_args.args,
        )
        self.assertEqual({"color": (112, 128, 144), "font": font, "scale_width": scale_size}, draw_ticks.call_args.kwargs)
        self.assertEqual([(14, "mono", "normal", "normal")], font_requests)
        self.assertEqual(
            {
                "center": center,
                "end": gauge_point(center, radius=radius, ratio=0.5, length_ratio=0.85),
                "accent_color": (64, 80, 96),
                "needle_color": (112, 128, 144),
                "scale_width": scale_size,
            },
            draw_pointer.call_args.kwargs,
        )

    def test_draw_gauge_progress_arcs_draws_track_and_progress_sweep(self) -> None:
        target = RecordingTarget()

        with patch("hud_pi.pygame_gauge_primitives.draw_aa_arc") as draw_arc:
            draw_gauge_progress_arcs(
                target,  # type: ignore[arg-type]
                center=(50, 60),
                radius=30,
                ratio=0.25,
                track_color=(1, 2, 3),
                progress_color=(4, 5, 6),
                width=6,
            )

        self.assertEqual(2, draw_arc.call_count)
        self.assertEqual((target, (1, 2, 3), (50, 60), 30, math.radians(135), math.radians(405), 6), draw_arc.call_args_list[0].args)
        self.assertEqual((target, (4, 5, 6), (50, 60), 30, math.radians(135), math.radians(202.5), 6), draw_arc.call_args_list[1].args)

    def test_draw_sport_gauge_arcs_draws_outer_track_and_redline_band(self) -> None:
        target = RecordingTarget()

        with patch("hud_pi.pygame_gauge_primitives.draw_aa_arc") as draw_arc:
            draw_sport_gauge_arcs(
                target,  # type: ignore[arg-type]
                center=(50, 60),
                radius=80,
                track_color=(1, 2, 3),
                redline_color=(4, 5, 6),
                scale_width=lambda width: width,
            )

        self.assertEqual(2, draw_arc.call_count)
        self.assertEqual((target, (1, 2, 3), (50, 60), 80, math.radians(135), math.radians(405), 4), draw_arc.call_args_list[0].args)
        self.assertEqual((target, (4, 5, 6), (50, 60), 70, math.radians(351), math.radians(405), 4), draw_arc.call_args_list[1].args)

    def test_draw_gauge_ticks_draws_lines_and_labels_with_scaled_width(self) -> None:
        target = RecordingTarget()
        font = RecordingFont()
        entries = (
            GaugeTickEntry((10, 20), (30, 40), True, 2, "0", (50, 60)),
            GaugeTickEntry((15, 25), (35, 45), False, 1, None, None),
        )

        with patch("hud_pi.pygame_gauge_primitives.pygame.draw.line") as draw_line:
            draw_gauge_ticks(
                target,  # type: ignore[arg-type]
                entries,
                color=(255, 255, 255),
                font=font,
                scale_width=lambda width: width * 2,
            )

        self.assertEqual(2, draw_line.call_count)
        self.assertEqual((target, (255, 255, 255), (10, 20), (30, 40), 4), draw_line.call_args_list[0].args)
        self.assertEqual([("0", (255, 255, 255))], font.rendered)
        self.assertEqual([(45, 57)], [rect.topleft for _surface, rect in target.blits])

    def test_draw_sport_gauge_ticks_uses_redline_major_and_minor_colors(self) -> None:
        target = RecordingTarget()
        font = RecordingFont()
        entries = (
            SportGaugeTickEntry((10, 20), (30, 40), True, False, 3, "1", (50, 60)),
            SportGaugeTickEntry((15, 25), (35, 45), False, False, 1, None, None),
            SportGaugeTickEntry((20, 30), (40, 50), True, True, 3, "8", (60, 70)),
        )

        with patch("hud_pi.pygame_gauge_primitives.pygame.draw.line") as draw_line:
            draw_sport_gauge_ticks(
                target,  # type: ignore[arg-type]
                entries,
                redline_color=(255, 0, 0),
                major_color=(255, 255, 255),
                minor_color=(26, 36, 48),
                font=font,
                scale_width=lambda width: width,
            )

        self.assertEqual((255, 255, 255), draw_line.call_args_list[0].args[1])
        self.assertEqual((26, 36, 48), draw_line.call_args_list[1].args[1])
        self.assertEqual((255, 0, 0), draw_line.call_args_list[2].args[1])
        self.assertEqual([("1", (255, 255, 255)), ("8", (255, 0, 0))], font.rendered)
        self.assertEqual([(45, 57), (55, 67)], [rect.topleft for _surface, rect in target.blits])

    def test_draw_gauge_pointer_draws_shadow_body_and_center_hub(self) -> None:
        target = RecordingTarget()

        with patch("hud_pi.pygame_gauge_primitives.pygame.draw.line") as draw_line, patch("hud_pi.pygame_gauge_primitives.pygame.draw.circle") as draw_circle:
            draw_gauge_pointer(
                target,  # type: ignore[arg-type]
                center=(50, 60),
                end=(80, 20),
                accent_color=(36, 211, 107),
                needle_color=(246, 251, 255),
                scale_width=lambda width: width,
            )

        self.assertEqual(3, draw_line.call_count)
        self.assertEqual((target, (0, 0, 0, 120), (52, 62), (82, 22), 6), draw_line.call_args_list[0].args)
        self.assertEqual((target, (36, 211, 107), (50, 60), (80, 20), 6), draw_line.call_args_list[1].args)
        self.assertEqual((target, (246, 251, 255), (50, 60), (80, 20), 2), draw_line.call_args_list[2].args)
        self.assertEqual((target, (246, 251, 255), (50, 60), 8), draw_circle.call_args_list[0].args)
        self.assertEqual((target, (36, 211, 107), (50, 60), 4), draw_circle.call_args_list[1].args)

    def test_draw_sport_gauge_pointer_draws_tail_body_and_hub(self) -> None:
        target = RecordingTarget()

        with patch("hud_pi.pygame_gauge_primitives.pygame.draw.line") as draw_line, patch("hud_pi.pygame_gauge_primitives.pygame.draw.circle") as draw_circle:
            draw_sport_gauge_pointer(
                target,  # type: ignore[arg-type]
                center=(50, 60),
                end=(90, 30),
                tail=(40, 70),
                redline_color=(255, 59, 48),
                scale_width=lambda width: width,
            )

        self.assertEqual((target, (0, 0, 0, 150), (43, 73), (93, 33), 6), draw_line.call_args_list[0].args)
        self.assertEqual((target, (255, 59, 48), (40, 70), (90, 30), 4), draw_line.call_args_list[1].args)
        self.assertEqual((target, (20, 25, 30), (50, 60), 16), draw_circle.call_args_list[0].args)
        self.assertEqual((target, (255, 59, 48), (50, 60), 12, 2), draw_circle.call_args_list[1].args)


if __name__ == "__main__":
    unittest.main()
