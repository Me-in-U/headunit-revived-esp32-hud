from __future__ import annotations

from dataclasses import dataclass


RectTuple = tuple[int, int, int, int]
Point = tuple[int, int]
Segment = tuple[Point, Point]


@dataclass(frozen=True)
class ValueBarGeometry:
    bar_rect: RectTuple
    fill_rect: RectTuple | None
    highlight_rect: RectTuple | None
    segment_lines: list[Segment]
    border_radius: int


def value_bar_highlight_color(fill_color: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple(min(255, channel + 40) for channel in fill_color)


def value_bar_geometry(
    rect: RectTuple,
    *,
    ratio: float,
    min_bar_height: int,
    segment_count: int = 10,
) -> ValueBarGeometry:
    rect_x, rect_y, rect_w, rect_h = rect
    rect_center_y = rect_y + rect_h // 2
    bar_height = max(min_bar_height, rect_h // 3)
    bar_rect = (rect_x, rect_center_y - bar_height // 2, rect_w, bar_height)
    border_radius = bar_height // 2

    fill_rect: RectTuple | None = None
    highlight_rect: RectTuple | None = None
    if ratio > 0:
        fill_width = max(bar_height, int(rect_w * ratio))
        fill_rect = (bar_rect[0], bar_rect[1], fill_width, bar_height)
        highlight_rect = (fill_rect[0], fill_rect[1], fill_rect[2], fill_rect[3] // 3)

    segment_lines: list[Segment] = []
    for index in range(1, max(1, segment_count)):
        x = bar_rect[0] + int(bar_rect[2] * index / segment_count)
        segment_lines.append(((x, bar_rect[1]), (x, bar_rect[1] + bar_rect[3])))

    return ValueBarGeometry(
        bar_rect=bar_rect,
        fill_rect=fill_rect,
        highlight_rect=highlight_rect,
        segment_lines=segment_lines,
        border_radius=border_radius,
    )
