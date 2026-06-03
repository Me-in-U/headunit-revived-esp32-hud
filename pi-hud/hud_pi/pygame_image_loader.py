from __future__ import annotations

import base64
import binascii
import io
import os
from pathlib import Path
from typing import Any

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame


ImageCache = tuple[str, pygame.Surface] | None


def image_source(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def load_pygame_image_source(source: str) -> pygame.Surface | None:
    source = image_source(source)
    if not source:
        return None
    try:
        if source.startswith("data:image/") and ";base64," in source:
            encoded = source.split(";base64,", 1)[1]
            data = base64.b64decode(encoded, validate=True)
            loaded = pygame.image.load(io.BytesIO(data))
        else:
            path = Path(source)
            if not path.exists():
                return None
            loaded = pygame.image.load(str(path))
        try:
            return loaded.convert_alpha()
        except pygame.error:
            return loaded.copy()
    except (OSError, ValueError, binascii.Error, pygame.error):
        return None


def load_cached_image_source(value: Any, cache: ImageCache) -> tuple[pygame.Surface | None, ImageCache]:
    source = image_source(value)
    if not source:
        return None, cache
    if cache and cache[0] == source:
        return cache[1], cache
    loaded = load_pygame_image_source(source)
    if loaded is None:
        return None, cache
    next_cache = (source, loaded)
    return loaded, next_cache
