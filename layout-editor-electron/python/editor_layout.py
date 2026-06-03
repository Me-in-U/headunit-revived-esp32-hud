from __future__ import annotations

import copy
from typing import Any

from editor_paths import ensure_pi_hud_path

ensure_pi_hud_path()

from hud_pi.layout import normalize_layout_for_save  # noqa: E402
from hud_pi.layout_verifier import build_layout_handoff, verify_layout  # noqa: E402


def ensure_screen_layout(layout: dict[str, Any], current_screen: str) -> None:
    screens = layout.setdefault("screens", {})
    if not isinstance(screens, dict):
        screens = {}
        layout["screens"] = screens
    base_elements = copy.deepcopy(layout.get("elements", []))
    for screen_name, label in (("standalone", "Standalone vehicle HUD"), ("bridge", "Bridge navigation HUD")):
        screen = screens.setdefault(screen_name, {"label": label, "elements": copy.deepcopy(base_elements)})
        if not isinstance(screen, dict):
            screens[screen_name] = {"label": label, "elements": copy.deepcopy(base_elements)}
            screen = screens[screen_name]
        if not isinstance(screen.get("elements"), list):
            screen["elements"] = copy.deepcopy(base_elements)
    if current_screen not in screens:
        current_screen = "standalone"
    layout["elements"] = copy.deepcopy(screens[current_screen]["elements"])


def sync_current_screen(layout: dict[str, Any], current_screen: str) -> None:
    screens = layout.get("screens")
    if not isinstance(screens, dict):
        screens = {}
        layout["screens"] = screens
    if current_screen not in screens or not isinstance(screens.get(current_screen), dict):
        screens[current_screen] = {"label": current_screen.title(), "elements": []}
    screens[current_screen]["elements"] = copy.deepcopy(layout.get("elements", []))


def prepare_for_screen(layout: dict[str, Any], current_screen: str) -> dict[str, Any]:
    sync_current_screen(layout, current_screen)
    return normalize_layout_for_save(layout)


def prepare_for_save(layout: dict[str, Any], current_screen: str) -> dict[str, Any]:
    prepared = prepare_for_screen(layout, current_screen)
    canvas = prepared["canvas"]
    result = verify_layout(prepared, width=canvas["width"], height=canvas["height"])
    if not result.ok:
        raise ValueError("\n".join(result.errors))
    prepared["pi_hud_handoff"] = build_layout_handoff(prepared, result.render_size, result.non_background_pixels)
    return prepared
