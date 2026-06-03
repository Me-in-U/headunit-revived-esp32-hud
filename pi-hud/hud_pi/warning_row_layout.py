from __future__ import annotations

from dataclasses import dataclass

from .display_format import warning_label


@dataclass(frozen=True)
class WarningRowEntry:
    binding: str
    label: str
    rect: tuple[int, int, int, int]


def warning_row_entries(
    bindings: list[str],
    *,
    rect: tuple[int, int, int, int],
    gap: int,
    language: str,
) -> list[WarningRowEntry]:
    if not bindings:
        return []
    rect_x, rect_y, rect_w, rect_h = rect
    step = max(1, rect_w // len(bindings))
    return [
        WarningRowEntry(
            binding=binding,
            label=warning_label(binding, language),
            rect=(rect_x + step * index, rect_y, step - gap, rect_h),
        )
        for index, binding in enumerate(bindings)
    ]
