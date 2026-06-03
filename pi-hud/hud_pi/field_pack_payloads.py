from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hud_pi.field_pack_manifest import PayloadEntry, relative_source
from hud_pi.vehicle_profiles import load_vehicle_profiles, profile_map


def vehicle_profile_payload_entries(layout: dict[str, Any], vehicle_profile_dirs: list[Path]) -> list[PayloadEntry]:
    profiles = profile_map(load_vehicle_profiles(vehicle_profile_dirs), layout)
    return [
        PayloadEntry(
            path=f"vehicles/{vehicle_id}.json",
            payload=json.dumps(profile, ensure_ascii=False, indent=2).encode("utf-8") + b"\n",
            source=f"vehicle_profile:{vehicle_id}",
        )
        for vehicle_id, profile in sorted(profiles.items())
    ]


def asset_payload_entries(warning_assets_dir: Path, nav_assets_dir: Path, repo_root: Path | None = None) -> list[PayloadEntry]:
    entries: list[PayloadEntry] = []
    for asset_path in sorted(path for path in warning_assets_dir.glob("*.png") if path.is_file()):
        entries.append(
            payload_entry_from_file(
                asset_path,
                archive_asset_path(asset_path, warning_assets_dir, "pi-hud/assets/warning-icons"),
                repo_root,
            )
        )
    for asset_path in sorted(path for path in nav_assets_dir.glob("*.png") if path.is_file()):
        entries.append(
            payload_entry_from_file(
                asset_path,
                archive_asset_path(asset_path, nav_assets_dir, "pi-hud/assets/nav-icons"),
                repo_root,
            )
        )
    return entries


def payload_entry_from_file(source: Path, archive_path: str, repo_root: Path | None = None) -> PayloadEntry:
    return PayloadEntry(
        path=archive_path,
        payload=source.read_bytes(),
        source=relative_source(source, repo_root) if repo_root else str(source),
    )


def archive_layout_path(layout_path: Path, repo_root: Path) -> str:
    layouts_dir = repo_root / "layouts"
    try:
        relative = layout_path.relative_to(layouts_dir)
        return f"layouts/{relative.as_posix()}"
    except ValueError:
        return f"layouts/{layout_path.name}"


def archive_asset_path(asset_path: Path, assets_dir: Path, archive_root: str) -> str:
    try:
        relative = asset_path.relative_to(assets_dir)
    except ValueError:
        relative = Path(asset_path.name)
    return f"{archive_root}/{relative.as_posix()}"


def readme_text(layout_archive_path: str) -> str:
    return f"""Headunit Pi HUD field pack

Contents:
- {layout_archive_path}
- vehicles/*.json
- pi-hud/assets/warning-icons/*.png
- pi-hud/assets/nav-icons/*.png
- config/pi-hud.env.example
- preview/layout-preview.png
- manifest.json

On the Raspberry Pi after pi-hud/scripts/install-pi.sh has installed the runtime:

  /opt/headunit-pi-hud/.venv/bin/python \\
    /opt/headunit-pi-hud/pi-hud/scripts/apply-field-pack.py \\
    headunit-pi-field-pack.zip

  /opt/headunit-pi-hud/.venv/bin/python \\
    /opt/headunit-pi-hud/pi-hud/scripts/acceptance-check.py --probe-display --probe-inputs --json

  sudo systemctl restart headunit-pi-hud.service

Acceptance output is written to:

  /opt/headunit-pi-hud/vehicle-baseline/acceptance-check.json

If /etc/headunit-pi-hud.env is already edited for the car, merge the new env example manually instead of overwriting it.
"""
