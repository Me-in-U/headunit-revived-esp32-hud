from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ViewportScale:
    x: float
    y: float


def viewport_scale(screen_size: tuple[int, int], canvas_size: tuple[int, int]) -> ViewportScale:
    screen_w, screen_h = screen_size
    canvas_w, canvas_h = canvas_size
    return ViewportScale(screen_w / canvas_w, screen_h / canvas_h)


def scale_x_value(value: float | int, scale: ViewportScale) -> int:
    return int(float(value) * scale.x)


def scale_y_value(value: float | int, scale: ViewportScale) -> int:
    return int(float(value) * scale.y)


def scale_size(value: float | int, scale: ViewportScale) -> int:
    return max(1, int(float(value) * min(scale.x, scale.y)))


def element_rect(element: dict[str, Any], scale: ViewportScale) -> tuple[int, int, int, int]:
    return (
        scale_x_value(element.get("x", 0), scale),
        scale_y_value(element.get("y", 0), scale),
        scale_x_value(element.get("w", 100), scale),
        scale_y_value(element.get("h", 40), scale),
    )
