from __future__ import annotations

import tempfile
from pathlib import Path

from hud_pi.field_pack_archive import write_field_pack
from hud_pi.field_pack_manifest import build_manifest
from hud_pi.field_pack_payloads import (
    archive_layout_path,
    asset_payload_entries,
    payload_entry_from_file,
)
from hud_pi.field_pack_requirements import require_directory, require_file
from hud_pi.field_pack_result import FieldPackResult
from hud_pi.layout import load_layout
from hud_pi.layout_verifier import verify_layout_file


def build_field_pack_from_file(
    *,
    layout_path: Path,
    vehicles_dir: Path,
    env_example_path: Path,
    warning_assets_dir: Path,
    nav_assets_dir: Path,
    output_path: Path,
    width: int = 1920,
    height: int = 480,
    require_handoff: bool = True,
    repo_root: Path | None = None,
) -> FieldPackResult:
    repo_root = repo_root or layout_path.resolve().parents[1]
    require_file(layout_path, "layout")
    require_file(env_example_path, "env example")
    require_directory(vehicles_dir, "vehicles dir")
    require_directory(warning_assets_dir, "warning assets dir")
    require_directory(nav_assets_dir, "nav assets dir")

    vehicle_paths = sorted(vehicles_dir.glob("*.json"))
    if not vehicle_paths:
        raise ValueError(f"vehicles dir has no JSON profiles: {vehicles_dir}")

    with tempfile.TemporaryDirectory(prefix="headunit-field-pack-") as temp_dir:
        preview_path = Path(temp_dir) / "layout-preview.png"
        verification = verify_layout_file(
            layout_path,
            width=width,
            height=height,
            output=preview_path,
            require_handoff=require_handoff,
        )
        if not verification.ok:
            raise ValueError("layout verification failed: " + "; ".join(verification.errors))

        layout = load_layout(layout_path)
        layout_entry = payload_entry_from_file(layout_path, archive_layout_path(layout_path, repo_root), repo_root)
        env_entry = payload_entry_from_file(env_example_path, "config/pi-hud.env.example", repo_root)
        preview_entry = payload_entry_from_file(preview_path, "preview/layout-preview.png", repo_root)
        vehicle_entries = [
            payload_entry_from_file(path, f"vehicles/{path.name}", repo_root)
            for path in vehicle_paths
        ]
        asset_entries = asset_payload_entries(warning_assets_dir, nav_assets_dir, repo_root)

        manifest = build_manifest(
            layout=layout,
            layout_entry=layout_entry,
            env_entry=env_entry,
            preview_entry=preview_entry,
            vehicle_entries=vehicle_entries,
            asset_entries=asset_entries,
            verification=verification,
            require_handoff=require_handoff,
        )
        write_field_pack(output_path, layout_entry, env_entry, preview_entry, vehicle_entries, asset_entries, manifest)

    return FieldPackResult(
        output=output_path,
        render_size=(verification.render_size[0], verification.render_size[1]),
        non_background_pixels=verification.non_background_pixels,
        manifest=manifest,
    )
