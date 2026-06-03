from __future__ import annotations

import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from hud_pi.field_pack_manifest import load_manifest, manifest_entries, target_path, verify_payloads
from hud_pi.layout_verifier import verify_layout_file


@dataclass(frozen=True)
class FieldPackApplyResult:
    app_dir: Path
    env_file: Path
    env_written: bool
    layout: Path
    vehicles: list[Path]
    assets: list[Path]


def apply_field_pack_package(
    *,
    package_path: Path,
    app_dir: Path,
    env_file: Path,
    overwrite_env: bool = False,
) -> FieldPackApplyResult:
    if not package_path.is_file():
        raise ValueError(f"package does not exist: {package_path}")

    with zipfile.ZipFile(package_path) as archive:
        manifest = load_manifest(archive)
        layout_entry, vehicle_entries, asset_entries, env_entry = manifest_entries(manifest)
        payloads = verify_payloads(archive, [layout_entry, *vehicle_entries, *asset_entries, env_entry])
        stage = stage_payloads(app_dir, layout_entry, vehicle_entries, asset_entries, payloads)
        env_written = write_env_file(env_file, env_entry, payloads, overwrite=overwrite_env)

    return FieldPackApplyResult(
        app_dir=app_dir,
        env_file=env_file,
        env_written=env_written,
        layout=stage["layout"],
        vehicles=stage["vehicles"],
        assets=stage["assets"],
    )


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
