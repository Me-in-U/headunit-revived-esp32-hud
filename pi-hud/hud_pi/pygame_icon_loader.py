from __future__ import annotations

import os
from pathlib import Path
from typing import MutableMapping

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from .icon_assets import clean_icon_name


def load_cached_png_icon(
    icon_name: str,
    icon_dir: Path,
    cache: MutableMapping[str, pygame.Surface],
) -> pygame.Surface | None:
    clean = clean_icon_name(icon_name)
    if not clean:
        return None
    if clean not in cache:
        path = icon_dir / f"{clean}.png"
        if not path.exists():
            return None
        loaded = pygame.image.load(str(path))
        try:
            loaded = loaded.convert_alpha()
        except pygame.error:
            loaded = loaded.copy()
        cache[clean] = loaded
    return cache[clean]
