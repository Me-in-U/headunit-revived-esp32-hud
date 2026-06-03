from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from editor_layout import ensure_screen_layout
from editor_palette import PALETTE
from editor_paths import (
    REPO_ROOT,
    default_env_example_path,
    default_layout_path,
    default_nav_icon_assets_dir,
    default_vehicle_profile_paths,
    default_warning_icon_assets_dir,
    ensure_pi_hud_path,
)

ensure_pi_hud_path()

from hud_pi.field_pack import build_field_pack_from_layout  # noqa: E402
from hud_pi.layout import normalize_layout_for_save  # noqa: E402
from hud_pi.vehicle_profiles import load_vehicle_profiles, profile_map  # noqa: E402


def metadata_response() -> dict[str, Any]:
    profiles = profile_map(load_vehicle_profiles(default_vehicle_profile_paths()), {})
    return {
        "ok": True,
        "repoRoot": str(REPO_ROOT),
        "defaultLayoutPath": str(default_layout_path()),
        "palette": PALETTE,
        "vehicles": sorted(profiles),
        "vehicleProfiles": profiles,
    }


def load_layout_response(path: Path) -> dict[str, Any]:
    layout = json.loads(path.read_text(encoding="utf-8"))
    layout = normalize_layout_for_save(layout)
    current_screen = "standalone"
    ensure_screen_layout(layout, current_screen)
    profiles = profile_map(load_vehicle_profiles(default_vehicle_profile_paths()), layout)
    return {
        "ok": True,
        "path": str(path),
        "layout": layout,
        "currentScreen": current_screen,
        "vehicles": sorted(profiles),
        "vehicleProfiles": profiles,
    }


def payload_layout(payload: dict[str, Any]) -> dict[str, Any]:
    layout = payload.get("layout")
    if not isinstance(layout, dict):
        raise ValueError("payload.layout must be an object")
    return copy.deepcopy(layout)


def render_size(layout: dict[str, Any], payload: dict[str, Any]) -> tuple[int, int]:
    canvas = layout.setdefault("canvas", {})
    width = int(payload.get("width") or canvas.get("width") or 1920)
    height = int(payload.get("height") or canvas.get("height") or 480)
    return max(1, width), max(1, height)


def verification_response(result: Any) -> dict[str, Any]:
    return {
        "ok": bool(result.ok),
        "errors": list(result.errors),
        "renderSize": [result.render_size[0], result.render_size[1]],
        "nonBackgroundPixels": result.non_background_pixels,
        "output": str(result.output) if result.output else "",
    }


def export_field_pack_response(layout: dict[str, Any], layout_path: Path, output: Path) -> dict[str, Any]:
    canvas = layout["canvas"]
    try:
        result = build_field_pack_from_layout(
            layout=layout,
            layout_path=layout_path,
            vehicle_profile_dirs=default_vehicle_profile_paths(),
            env_example_path=default_env_example_path(),
            warning_assets_dir=default_warning_icon_assets_dir(),
            nav_assets_dir=default_nav_icon_assets_dir(),
            output_path=output,
            width=canvas["width"],
            height=canvas["height"],
            require_handoff=True,
        )
    except ValueError as error:
        return {"ok": False, "errors": [str(error)]}

    return {
        "ok": True,
        "errors": [],
        "output": str(result.output),
        "renderSize": [result.render_size[0], result.render_size[1]],
        "nonBackgroundPixels": result.non_background_pixels,
    }
