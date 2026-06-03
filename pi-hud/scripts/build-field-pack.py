#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
PI_HUD_DIR = ROOT_DIR / "pi-hud"
if str(PI_HUD_DIR) not in sys.path:
    sys.path.insert(0, str(PI_HUD_DIR))

from hud_pi.layout import load_layout
from hud_pi.layout_verifier import verify_layout_file


DEFAULT_LAYOUT = "layouts/avante_hd_2010_default.json"
DEFAULT_VEHICLES_DIR = "vehicles"
DEFAULT_ENV_EXAMPLE = "pi-hud/config/pi-hud.env.example"
DEFAULT_ASSETS_DIR = "pi-hud/assets/warning-icons"
DEFAULT_NAV_ASSETS_DIR = "pi-hud/assets/nav-icons"
DEFAULT_OUTPUT = "field-pack/headunit-pi-field-pack.zip"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a Raspberry Pi HUD field-transfer package")
    parser.add_argument("--layout", default=DEFAULT_LAYOUT, help="Layout JSON to place under layouts/ in the zip")
    parser.add_argument("--vehicles-dir", default=DEFAULT_VEHICLES_DIR, help="Directory of vehicle profile JSON files")
    parser.add_argument("--env-example", default=DEFAULT_ENV_EXAMPLE, help="Environment example copied as config/pi-hud.env.example")
    parser.add_argument("--assets-dir", default=DEFAULT_ASSETS_DIR, help="Warning icon assets copied into pi-hud/assets/")
    parser.add_argument("--nav-assets-dir", default=DEFAULT_NAV_ASSETS_DIR, help="Navigation icon assets copied into pi-hud/assets/")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output zip path")
    parser.add_argument("--width", type=int, default=1920, help="Expected HUD render width")
    parser.add_argument("--height", type=int, default=480, help="Expected HUD render height")
    handoff = parser.add_mutually_exclusive_group()
    handoff.add_argument("--require-handoff", dest="require_handoff", action="store_true", default=True)
    handoff.add_argument("--no-require-handoff", dest="require_handoff", action="store_false")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        package = build_field_pack(args)
    except ValueError as error:
        print(f"[FAIL] {error}", file=sys.stderr)
        return 1

    print(f"[OK] wrote {package}")
    return 0


def build_field_pack(args: argparse.Namespace) -> Path:
    layout_path = resolve_path(args.layout)
    vehicles_dir = resolve_path(args.vehicles_dir)
    env_example_path = resolve_path(args.env_example)
    assets_dir = resolve_path(args.assets_dir)
    nav_assets_dir = resolve_path(args.nav_assets_dir)
    output_path = resolve_path(args.output)

    require_file(layout_path, "layout")
    require_file(env_example_path, "env example")
    require_directory(vehicles_dir, "vehicles dir")
    require_directory(assets_dir, "assets dir")
    require_directory(nav_assets_dir, "nav assets dir")

    with tempfile.TemporaryDirectory(prefix="headunit-field-pack-") as temp_dir:
        preview_path = Path(temp_dir) / "layout-preview.png"
        verification = verify_layout_file(
            layout_path,
            width=args.width,
            height=args.height,
            output=preview_path,
            require_handoff=args.require_handoff,
        )
        if not verification.ok:
            raise ValueError("layout verification failed: " + "; ".join(verification.errors))

        layout = load_layout(layout_path)
        selected_vehicle = str(layout.get("selected_vehicle", "")).strip()
        vehicle_paths = sorted(vehicles_dir.glob("*.json"))
        if not vehicle_paths:
            raise ValueError(f"vehicles dir has no JSON profiles: {vehicles_dir}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        layout_entry = file_entry(layout_path, archive_layout_path(layout_path))
        env_entry = file_entry(env_example_path, "config/pi-hud.env.example")
        preview_entry = file_entry(preview_path, "preview/layout-preview.png")
        vehicle_entries = [file_entry(path, f"vehicles/{path.name}") for path in vehicle_paths]
        asset_paths = sorted(path for path in assets_dir.glob("*.png") if path.is_file())
        nav_asset_paths = sorted(path for path in nav_assets_dir.glob("*.png") if path.is_file())
        asset_entries = [file_entry(path, archive_warning_asset_path(path, assets_dir)) for path in asset_paths]
        asset_entries.extend(file_entry(path, archive_nav_asset_path(path, nav_assets_dir)) for path in nav_asset_paths)

        manifest: dict[str, Any] = {
            "kind": "headunit-pi-field-pack",
            "schema_version": 1,
            "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "selected_vehicle": selected_vehicle,
            "layout": {
                **layout_entry,
                "render_size": [verification.render_size[0], verification.render_size[1]],
                "non_background_pixels": verification.non_background_pixels,
                "require_handoff": bool(args.require_handoff),
            },
            "preview": {
                **preview_entry,
                "render_size": [verification.render_size[0], verification.render_size[1]],
                "non_background_pixels": verification.non_background_pixels,
            },
            "vehicles": vehicle_entries,
            "assets": asset_entries,
            "env_example": env_entry,
            "install_targets": {
                "app_dir": "/opt/headunit-pi-hud",
                "env_file": "/etc/headunit-pi-hud.env",
                "layout": f"/opt/headunit-pi-hud/{layout_entry['path']}",
            },
        }

        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            write_file(archive, layout_path, layout_entry["path"])
            for vehicle_path, vehicle_entry in zip(vehicle_paths, vehicle_entries):
                write_file(archive, vehicle_path, vehicle_entry["path"])
            for asset_path, asset_entry in zip(asset_paths, asset_entries):
                write_file(archive, asset_path, asset_entry["path"])
            for asset_path, asset_entry in zip(nav_asset_paths, asset_entries[len(asset_paths) :]):
                write_file(archive, asset_path, asset_entry["path"])
            write_file(archive, env_example_path, env_entry["path"])
            write_file(archive, preview_path, preview_entry["path"])
            archive.writestr("README-pi-field-pack.txt", readme_text(layout_entry["path"]))
            archive.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n")

    return output_path


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT_DIR / path


def require_file(path: Path, label: str) -> None:
    if not path.is_file():
        raise ValueError(f"{label} does not exist: {path}")


def require_directory(path: Path, label: str) -> None:
    if not path.is_dir():
        raise ValueError(f"{label} does not exist: {path}")


def archive_layout_path(layout_path: Path) -> str:
    layouts_dir = ROOT_DIR / "layouts"
    try:
        relative = layout_path.relative_to(layouts_dir)
        return f"layouts/{relative.as_posix()}"
    except ValueError:
        return f"layouts/{layout_path.name}"


def archive_warning_asset_path(asset_path: Path, assets_dir: Path) -> str:
    try:
        relative = asset_path.relative_to(assets_dir)
    except ValueError:
        relative = Path(asset_path.name)
    return f"pi-hud/assets/warning-icons/{relative.as_posix()}"


def archive_nav_asset_path(asset_path: Path, assets_dir: Path) -> str:
    try:
        relative = asset_path.relative_to(assets_dir)
    except ValueError:
        relative = Path(asset_path.name)
    return f"pi-hud/assets/nav-icons/{relative.as_posix()}"


def file_entry(source: Path, archive_path: str) -> dict[str, Any]:
    payload = source.read_bytes()
    return {
        "path": archive_path,
        "source": source.relative_to(ROOT_DIR).as_posix() if is_relative_to(source, ROOT_DIR) else str(source),
        "size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def write_file(archive: zipfile.ZipFile, source: Path, archive_path: str) -> None:
    archive.write(source, archive_path)


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


if __name__ == "__main__":
    raise SystemExit(main())
