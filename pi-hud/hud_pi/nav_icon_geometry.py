from __future__ import annotations

from dataclasses import dataclass


RectTuple = tuple[int, int, int, int]
Point = tuple[int, int]
Segment = tuple[Point, Point]


@dataclass(frozen=True)
class CornerArrowShape:
    polyline: list[Point]
    head_segments: list[Segment]


@dataclass(frozen=True)
class UTurnShape:
    arc_rect: tuple[int, int, int, int]
    line_segment: Segment
    head_segments: list[Segment]


def lucide_point(rect: RectTuple, x: float, y: float) -> Point:
    rect_x, rect_y, rect_w, rect_h = rect
    inset = min(rect_w, rect_h) * 0.06
    width = max(1.0, rect_w - inset * 2)
    height = max(1.0, rect_h - inset * 2)
    return (int(rect_x + inset + width * x / 24), int(rect_y + inset + height * y / 24))


def straight_arrow_segments(rect: RectTuple) -> list[Segment]:
    tip = lucide_point(rect, 12, 5)
    return [
        (lucide_point(rect, 12, 19), tip),
        (lucide_point(rect, 5, 12), tip),
        (lucide_point(rect, 19, 12), tip),
    ]


def corner_arrow_shape(rect: RectTuple, direction: str) -> CornerArrowShape:
    if direction == "left":
        arrow_tip = lucide_point(rect, 4, 9)
        return CornerArrowShape(
            polyline=[
                lucide_point(rect, 20, 20),
                lucide_point(rect, 20, 13),
                lucide_point(rect, 16, 9),
                arrow_tip,
            ],
            head_segments=[
                (lucide_point(rect, 9, 14), arrow_tip),
                (lucide_point(rect, 9, 4), arrow_tip),
            ],
        )
    arrow_tip = lucide_point(rect, 20, 9)
    return CornerArrowShape(
        polyline=[
            lucide_point(rect, 4, 20),
            lucide_point(rect, 4, 13),
            lucide_point(rect, 8, 9),
            arrow_tip,
        ],
        head_segments=[
            (lucide_point(rect, 15, 14), arrow_tip),
            (lucide_point(rect, 15, 4), arrow_tip),
        ],
    )


def arrow_head_segments(point: Point, direction: str, line_width: int) -> list[Segment]:
    size = max(8, line_width * 2)
    x, y = point
    if direction == "right":
        return [((x - size, y - size), point), ((x - size, y + size), point)]
    if direction == "down":
        return [((x - size, y - size), point), ((x + size, y - size), point)]
    return [((x + size, y - size), point), ((x + size, y + size), point)]


def uturn_shape(rect: RectTuple, line_width: int) -> UTurnShape:
    _, _, rect_w, rect_h = rect
    arc_x, arc_y = lucide_point(rect, 4, 4)
    arrow_point = lucide_point(rect, 6, 12)
    return UTurnShape(
        arc_rect=(arc_x, arc_y, max(1, int(rect_w * 0.5)), max(1, int(rect_h * 0.5))),
        line_segment=(lucide_point(rect, 18, 20), lucide_point(rect, 18, 12)),
        head_segments=arrow_head_segments(arrow_point, "down", line_width),
    )
