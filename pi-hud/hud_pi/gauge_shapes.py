from __future__ import annotations

import math

from .gauge_values import gauge_angle_radians, polar_point


def analog_gauge_geometry(rect: tuple[int, int, int, int]) -> tuple[tuple[int, int], int]:
    x, y, width, height = rect
    center = (x + width // 2, y + height // 2 + height // 8)
    radius = max(8, min(width // 2, int(height * 0.66)))
    return center, radius


def needle_gauge_geometry(rect: tuple[int, int, int, int]) -> tuple[tuple[int, int], int]:
    x, y, width, height = rect
    center = (x + width // 2, y + height - max(4, height // 8))
    radius = max(8, min(width // 2, int(height * 0.78)))
    return center, radius


def sport_gauge_geometry(rect: tuple[int, int, int, int]) -> tuple[tuple[int, int], int]:
    x, y, width, height = rect
    center = (x + width // 2, y + height // 2 + height // 6)
    radius = max(8, min(width // 2, int(height * 0.62)))
    return center, radius


def sport_gauge_needle_shape(
    *,
    center: tuple[int, int],
    radius: int,
    ratio: float,
    needle_length_ratio: float = 0.95,
    tail_length_ratio: float = 0.20,
) -> tuple[tuple[int, int], tuple[int, int]]:
    angle = gauge_angle_radians(ratio)
    needle_len = radius * needle_length_ratio
    tail_len = radius * tail_length_ratio
    end = polar_point(center, needle_len, angle)
    tail = (
        center[0] - int(math.cos(angle) * tail_len),
        center[1] - int(math.sin(angle) * tail_len),
    )
    return end, tail
