from __future__ import annotations

from collections.abc import Callable
import os
from typing import Any, Protocol

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from .gear_indicator import GearIndicatorEntry, gear_indicator_entries


class BlitTarget(Protocol):
    def blit(self, surface: pygame.Surface, target: pygame.Rect) -> object:
        ...


def draw_gear_indicator_element(
    target: BlitTarget,
    element: dict[str, Any],
    *,
    rect: tuple[int, int, int, int],
    resolve: Callable[[str, Any], Any],
    font_factory: Callable[[int, str, str, str], Any],
) -> None:
    binding = str(element.get("binding", "vehicle.gear_range"))
    draw_gear_indicator_entries(
        target,
        gear_indicator_entries(element, resolve(binding, "--"), rect=rect),
        font_factory=font_factory,
    )


def draw_gear_indicator_entries(
    target: BlitTarget,
    entries: tuple[GearIndicatorEntry, ...],
    *,
    font_factory: Callable[[int, str, str, str], Any],
) -> None:
    for entry in entries:
        slot = pygame.Rect(entry.rect)
        font = font_factory(entry.font_size, entry.font_family, entry.font_weight, entry.font_style)
        surface = font.render(entry.label, True, entry.color)
        target.blit(surface, surface.get_rect(center=slot.center))
