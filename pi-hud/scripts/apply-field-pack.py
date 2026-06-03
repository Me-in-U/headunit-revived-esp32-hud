#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


PI_DIR = Path(__file__).resolve().parents[1]
if str(PI_DIR) not in sys.path:
    sys.path.insert(0, str(PI_DIR))

from hud_pi.layout_verifier import verify_layout_file


DEFAULT_APP_DIR = "/opt/headunit-pi-hud"
DEFAULT_ENV_FILE = "/etc/headunit-pi-hud.env"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify and apply a Raspberry Pi HUD field-transfer package")
    parser.add_argument("package", help="headunit-pi-field-pack.zip")
    parser.add_argument("--app-dir", default=DEFAULT_APP_DIR, help="Installed Pi HUD app directory")
    parser.add_argument("--env-file", default=DEFAULT_ENV_FILE, help="Runtime environment file")
    parser.add_argument("--overwrite-env", action="store_true", help="Replace env-file with config/pi-hud.env.example")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = apply_field_pack(args)
    except ValueError as error:
        print(f"[FAIL] {error}", file=sys.stderr)
        return 1

    print(f"[OK] applied {report['layout']} to {report['app_dir']}")
    if report["env_written"]:
        print(f"[OK] wrote env file {report['env_file']}")
    else:
        print(f"[SKIP] preserved existing env file {report['env_file']}")
    return 0


def apply_field_pack(args: argparse.Namespace) -> dict[str, Any]:
    package_path = Path(args.package)
    app_dir = Path(args.app_dir)
    env_file = Path(args.env_file)
    if not package_path.is_file():
        raise ValueError(f"package does not exist: {package_path}")

    with zipfile.ZipFile(package_path) as archive:
        manifest = load_manifest(archive)
        layout_entry, vehicle_entries, asset_entries, env_entry = manifest_entries(manifest)
        payloads = verify_payloads(archive, [layout_entry, *vehicle_entries, *asset_entries, env_entry])
        stage = stage_payloads(app_dir, layout_entry, vehicle_entries, asset_entries, payloads)
        env_written = write_env_file(env_file, env_entry, payloads, overwrite=args.overwrite_env)

    return {
        "app_dir": str(app_dir),
        "env_file": str(env_file),
        "env_written": env_written,
        "layout": str(stage["layout"]),
        "vehicles": [str(path) for path in stage["vehicles"]],
    }


def load_manifest(archive: zipfile.ZipFile) -> dict[str, Any]:
    try:
        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
    except KeyError as error:
        raise ValueError("manifest.json is missing") from error
    except json.JSONDecodeError as error:
        raise ValueError("manifest.json is not valid JSON") from error
    if not isinstance(manifest, dict):
        raise ValueError("manifest.json must be an object")
    if manifest.get("kind") != "headunit-pi-field-pack":
        raise ValueError("manifest kind is not headunit-pi-field-pack")
    if manifest.get("schema_version") != 1:
        raise ValueError("manifest schema_version must be 1")
    return manifest


def manifest_entries(manifest: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    layout = require_entry(manifest.get("layout"), "layout")
    vehicles = manifest.get("vehicles", [])
    if not isinstance(vehicles, list):
        raise ValueError("manifest vehicles must be a list")
    vehicle_entries = [require_entry(vehicle, f"vehicles[{index}]") for index, vehicle in enumerate(vehicles)]
    assets = manifest.get("assets", [])
    if not isinstance(assets, list):
        raise ValueError("manifest assets must be a list")
    asset_entries = [require_entry(asset, f"assets[{index}]") for index, asset in enumerate(assets)]
    env_example = require_entry(manifest.get("env_example"), "env_example")
    return layout, vehicle_entries, asset_entries, env_example


def require_entry(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"manifest {label} must be an object")
    path = value.get("path")
    digest = value.get("sha256")
    if not isinstance(path, str) or not path.strip():
        raise ValueError(f"manifest {label}.path is missing")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError(f"manifest {label}.sha256 is missing")
    validate_archive_path(path)
    return value


def verify_payloads(archive: zipfile.ZipFile, entries: list[dict[str, Any]]) -> dict[str, bytes]:
    payloads: dict[str, bytes] = {}
    for entry in entries:
        archive_path = entry["path"]
        try:
            payload = archive.read(archive_path)
        except KeyError as error:
            raise ValueError(f"package file is missing: {archive_path}") from error
        digest = hashlib.sha256(payload).hexdigest()
        if digest.lower() != str(entry["sha256"]).lower():
            raise ValueError(f"sha256 mismatch for {archive_path}")
        payloads[archive_path] = payload
    return payloads


def stage_payloads(
    app_dir: Path,
    layout_entry: dict[str, Any],
    vehicle_entries: list[dict[str, Any]],
    asset_entries: list[dict[str, Any]],
    payloads: dict[str, bytes],
) -> dict[str, Any]:
    layout_target = target_path(app_dir, layout_entry["path"], required_prefix="layouts")
    vehicle_targets = [target_path(app_dir, entry["path"], required_prefix="vehicles") for entry in vehicle_entries]
    asset_targets = [target_path(app_dir, entry["path"], required_prefix="pi-hud/assets") for entry in asset_entries]
    with tempfile.TemporaryDirectory(prefix=".field-pack-", dir=str(app_dir.parent if app_dir.parent.exists() else None)) as temp_dir:
        temp_root = Path(temp_dir)
        temp_layout = temp_root / layout_entry["path"]
        write_bytes(temp_layout, payloads[layout_entry["path"]])
        temp_vehicles: list[Path] = []
        for entry in vehicle_entries:
            temp_vehicle = temp_root / entry["path"]
            write_bytes(temp_vehicle, payloads[entry["path"]])
            temp_vehicles.append(temp_vehicle)
        temp_assets: list[Path] = []
        for entry in asset_entries:
            temp_asset = temp_root / entry["path"]
            write_bytes(temp_asset, payloads[entry["path"]])
            temp_assets.append(temp_asset)

        verify_staged_layout(temp_layout, layout_entry)
        write_bytes(layout_target, temp_layout.read_bytes())
        for temp_vehicle, target in zip(temp_vehicles, vehicle_targets):
            write_bytes(target, temp_vehicle.read_bytes())
        for temp_asset, target in zip(temp_assets, asset_targets):
            write_bytes(target, temp_asset.read_bytes())

    return {"layout": layout_target, "vehicles": vehicle_targets, "assets": asset_targets}


def verify_staged_layout(layout_path: Path, layout_entry: dict[str, Any]) -> None:
    render_size = layout_entry.get("render_size", [1920, 480])
    width = int(render_size[0]) if isinstance(render_size, list) and len(render_size) >= 1 else 1920
    height = int(render_size[1]) if isinstance(render_size, list) and len(render_size) >= 2 else 480
    result = verify_layout_file(
        layout_path,
        width=width,
        height=height,
        require_handoff=bool(layout_entry.get("require_handoff", False)),
    )
    if not result.ok:
        raise ValueError("layout verification failed: " + "; ".join(result.errors))


def write_env_file(env_file: Path, env_entry: dict[str, Any], payloads: dict[str, bytes], overwrite: bool) -> bool:
    if env_file.exists() and not overwrite:
        return False
    write_bytes(env_file, payloads[env_entry["path"]])
    return True


def target_path(app_dir: Path, archive_path: str, required_prefix: str) -> Path:
    parts = PurePosixPath(archive_path).parts
    prefix_parts = PurePosixPath(required_prefix).parts
    if len(parts) < len(prefix_parts) or parts[: len(prefix_parts)] != prefix_parts:
        raise ValueError(f"{archive_path} must be under {required_prefix}/")
    relative = Path(*parts)
    target = app_dir / relative
    resolved_app = app_dir.resolve(strict=False)
    resolved_target = target.resolve(strict=False)
    if not is_relative_to(resolved_target, resolved_app):
        raise ValueError(f"target path escapes app dir: {archive_path}")
    return target


def validate_archive_path(path: str) -> None:
    archive_path = PurePosixPath(path)
    if archive_path.is_absolute() or any(part in ("", ".", "..") for part in archive_path.parts):
        raise ValueError(f"unsafe archive path: {path}")
    if "\\" in path:
        raise ValueError(f"archive path must use forward slashes: {path}")


def write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, dir=str(path.parent)) as handle:
        temp_path = Path(handle.name)
        handle.write(payload)
    try:
        shutil.move(str(temp_path), path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    raise SystemExit(main())
