from __future__ import annotations

from collections.abc import Callable
import os
from typing import Any

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from .display_format import DEFAULT_LANGUAGE, normalize_language
from .font_config import font_request


FontCache = dict[tuple[int, str, str, str, str], Any]


def load_cached_font(
    cache: FontCache,
    size: int,
    family: str | None = "default",
    weight: str | None = "normal",
    style: str | None = "normal",
    language: str | None = None,
    *,
    scale_size: Callable[[int], int] = lambda value: value,
) -> Any:
    normalized_family = family or "default"
    normalized_weight = weight or "normal"
    normalized_style = style or "normal"
    normalized_language = normalize_language(language or DEFAULT_LANGUAGE)
    key = (size, normalized_family, normalized_weight, normalized_style, normalized_language)
    if key not in cache:
        bold = normalized_weight == "bold"
        italic = normalized_style == "italic"
        scaled_size = max(8, scale_size(size))
        request = font_request(normalized_family, normalized_language)
        if request.backend == "builtin":
            font = pygame.font.Font(None, scaled_size)
            font.set_bold(bold)
            font.set_italic(italic)
        else:
            font = pygame.font.SysFont(str(request.family), scaled_size, bold=bold, italic=italic)
        cache[key] = font
    return cache[key]
