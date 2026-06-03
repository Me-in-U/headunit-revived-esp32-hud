from __future__ import annotations

import copy
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from .layout import color_tuple, load_layout, validate_layout
from .renderer import HudRenderer
from .state import HudState


HANDOFF_SCHEMA_VERSION = 1
HANDOFF_TARGET = "raspberry_pi"
HANDOFF_RENDERER = "hud_pi.renderer.HudRenderer"


@dataclass(frozen=True)
class LayoutVerificationResult:
    ok: bool
    errors: list[str]
    render_size: tuple[int, int]
    non_background_pixels: int
    output: Path | None = None


def build_layout_handoff(
    layout: dict[str, Any],
    render_size: tuple[int, int],
    non_background_pixels: int,
    verified_at_utc: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": HANDOFF_SCHEMA_VERSION,
        "target": HANDOFF_TARGET,
        "renderer": HANDOFF_RENDERER,
        "render_size": [render_size[0], render_size[1]],
        "non_background_pixels": non_background_pixels,
        "selected_vehicle": layout.get("selected_vehicle", ""),
        "layout_sha256": layout_content_sha256(layout),
        "verified_at_utc": verified_at_utc or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }


def layout_content_sha256(layout: dict[str, Any]) -> str:
    canonical = copy.deepcopy(layout)
    canonical.pop("pi_hud_handoff", None)
    payload = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_layout_handoff(layout: dict[str, Any], render_size: tuple[int, int]) -> list[str]:
    handoff = layout.get("pi_hud_handoff")
    if not isinstance(handoff, dict):
        return ["pi_hud_handoff metadata is missing"]

    errors: list[str] = []
    if handoff.get("schema_version") != HANDOFF_SCHEMA_VERSION:
        errors.append(f"pi_hud_handoff schema_version must be {HANDOFF_SCHEMA_VERSION}")
    if handoff.get("target") != HANDOFF_TARGET:
        errors.append(f"pi_hud_handoff target must be {HANDOFF_TARGET}")
    if handoff.get("renderer") != HANDOFF_RENDERER:
        errors.append(f"pi_hud_handoff renderer must be {HANDOFF_RENDERER}")
    if handoff.get("render_size") != [render_size[0], render_size[1]]:
        errors.append(f"pi_hud_handoff render_size must be {render_size[0]}x{render_size[1]}")
    if handoff.get("selected_vehicle") != layout.get("selected_vehicle", ""):
        errors.append("pi_hud_handoff selected_vehicle does not match layout selected_vehicle")
    if handoff.get("layout_sha256") != layout_content_sha256(layout):
        errors.append("pi_hud_handoff layout_sha256 does not match layout content")
    return errors


def verify_layout_file(
    path: str | Path,
    width: int = 1920,
    height: int = 480,
    output: str | Path | None = None,
    require_handoff: bool = False,
) -> LayoutVerificationResult:
    layout = load_layout(path)
    return verify_layout(layout, width=width, height=height, output=output, require_handoff=require_handoff)


def verify_layout(
    layout: dict[str, Any],
    width: int = 1920,
    height: int = 480,
    output: str | Path | None = None,
    require_handoff: bool = False,
) -> LayoutVerificationResult:
    errors = validate_layout(layout)
    render_width = max(1, int(width))
    render_height = max(1, int(height))
    render_size = (render_width, render_height)
    if require_handoff:
        errors.extend(validate_layout_handoff(layout, render_size))

    pygame.font.init()
    surface = pygame.Surface(render_size)
    HudRenderer(layout, surface).render(HudState.from_layout(layout))
    output_path = Path(output) if output else None
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(surface, str(output_path))

    non_background_pixels = count_non_background_pixels(surface, color_tuple(layout.get("canvas", {}).get("background", "#000000"), (0, 0, 0)))
    if non_background_pixels == 0:
        errors.append(f"layout rendered blank at {render_width}x{render_height}")
    return LayoutVerificationResult(
        ok=not errors,
        errors=errors,
        render_size=render_size,
        non_background_pixels=non_background_pixels,
        output=output_path,
    )


def count_non_background_pixels(surface: pygame.Surface, background: tuple[int, int, int]) -> int:
    width, height = surface.get_size()
    count = 0
    for y in range(height):
        for x in range(width):
            if surface.get_at((x, y))[:3] != background:
                count += 1
    return count
