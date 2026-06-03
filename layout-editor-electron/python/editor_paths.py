from __future__ import annotations

import os
import sys
from pathlib import Path


DEFAULT_LAYOUT_NAME = "avante_hd_2010_default.json"
REPO_ROOT = Path(__file__).resolve().parents[2]
PI_HUD_PATH = REPO_ROOT / "pi-hud"


def ensure_pi_hud_path() -> None:
    if PI_HUD_PATH.exists() and str(PI_HUD_PATH) not in sys.path:
        sys.path.insert(0, str(PI_HUD_PATH))


def bundled_root() -> Path:
    return REPO_ROOT


def first_existing(candidates: list[Path]) -> Path:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def default_layout_path() -> Path:
    env_layout = os.environ.get("HEADUNIT_HUD_LAYOUT")
    if env_layout:
        return Path(env_layout)
    return first_existing(
        [
            bundled_root() / "layouts" / DEFAULT_LAYOUT_NAME,
            REPO_ROOT / "layouts" / DEFAULT_LAYOUT_NAME,
            Path.cwd() / "layouts" / DEFAULT_LAYOUT_NAME,
        ]
    )


def default_vehicle_profile_paths() -> list[Path]:
    candidates = [
        bundled_root() / "vehicles",
        REPO_ROOT / "vehicles",
        Path.cwd() / "vehicles",
    ]
    return [candidate for candidate in candidates if candidate.exists()]


def default_env_example_path() -> Path:
    return first_existing(
        [
            bundled_root() / "pi-hud" / "config" / "pi-hud.env.example",
            REPO_ROOT / "pi-hud" / "config" / "pi-hud.env.example",
            Path.cwd() / "pi-hud" / "config" / "pi-hud.env.example",
        ]
    )


def default_warning_icon_assets_dir() -> Path:
    return first_existing(
        [
            bundled_root() / "pi-hud" / "assets" / "warning-icons",
            REPO_ROOT / "pi-hud" / "assets" / "warning-icons",
            Path.cwd() / "pi-hud" / "assets" / "warning-icons",
        ]
    )


def default_nav_icon_assets_dir() -> Path:
    return first_existing(
        [
            bundled_root() / "pi-hud" / "assets" / "nav-icons",
            REPO_ROOT / "pi-hud" / "assets" / "nav-icons",
            Path.cwd() / "pi-hud" / "assets" / "nav-icons",
        ]
    )
