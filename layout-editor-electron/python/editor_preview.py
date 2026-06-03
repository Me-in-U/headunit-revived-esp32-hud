from __future__ import annotations

import copy
import os
from io import BytesIO
from typing import Any

from editor_paths import ensure_pi_hud_path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ensure_pi_hud_path()

import pygame  # noqa: E402
from hud_pi.renderer import HudRenderer  # noqa: E402
from hud_pi.state import HudState  # noqa: E402


def render_preview_png(layout: dict[str, Any], width: int, height: int) -> bytes:
    pygame.font.init()
    preview_layout = copy.deepcopy(layout)
    preview_layout.pop("screens", None)
    state = HudState.from_layout(preview_layout)
    warnings = state.values.setdefault("warnings", {})
    for element in preview_layout.get("elements", []):
        if not isinstance(element, dict) or element.get("type") != "warning_icon":
            continue
        binding = str(element.get("binding", "")).strip()
        if binding.startswith("warnings."):
            warnings[binding.split(".", 1)[1]] = True
    surface = pygame.Surface((width, height))
    HudRenderer(preview_layout, surface).render(state)
    buffer = BytesIO()
    pygame.image.save(surface, buffer, "preview.png")
    return buffer.getvalue()
