from __future__ import annotations

from pathlib import Path


WARNING_ICON_DIR = Path(__file__).resolve().parents[1] / "assets" / "warning-icons"
NAV_ICON_DIR = Path(__file__).resolve().parents[1] / "assets" / "nav-icons"
MATERIAL_NAV_ICON_SOURCE = "@material-design-icons/svg 0.14.15 Apache-2.0 https://github.com/marella/material-design-icons"


def clean_icon_name(icon_name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in icon_name.strip().lower())


def icon_filename(icon_name: str) -> str:
    clean = clean_icon_name(icon_name)
    return f"{clean}.png" if clean else ""
