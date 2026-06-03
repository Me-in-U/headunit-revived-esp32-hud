from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from hud_pi.field_pack_archive import write_field_pack
from hud_pi.field_pack_defaults import DEFAULT_LAYOUT
from hud_pi.field_pack_manifest import PayloadEntry, build_manifest
from hud_pi.field_pack_payloads import (
    asset_payload_entries,
    payload_entry_from_file,
    vehicle_profile_payload_entries,
)
from hud_pi.field_pack_requirements import require_directory, require_file
from hud_pi.field_pack_result import FieldPackResult
from hud_pi.layout_verifier import verify_layout


def build_field_pack_from_layout(
    *,
    layout: dict[str, Any],
    layout_path: Path,
    vehicle_profile_dirs: list[Path],
    env_example_path: Path,
    warning_assets_dir: Path,
    nav_assets_dir: Path,
    output_path: Path,
    width: int,
    height: int,
    require_handoff: bool = True,
) -> FieldPackResult:
    require_file(env_example_path, "Pi HUD env example")
    require_directory(warning_assets_dir, "Pi HUD warning icon assets")
    require_directory(nav_assets_dir, "Pi HUD navigation icon assets")

    with tempfile.TemporaryDirectory(prefix="headunit-editor-field-pack-") as temp_dir:
        preview_path = Path(temp_dir) / "layout-preview.png"
        verification = verify_layout(
            layout,
            width=width,
            height=height,
            output=preview_path,
            require_handoff=require_handoff,
        )
        if not verification.ok:
            raise ValueError("layout verification failed: " + "; ".join(verification.errors))

        layout_name = layout_path.name or Path(DEFAULT_LAYOUT).name
        layout_entry = PayloadEntry(
            path=f"layouts/{layout_name}",
            payload=json.dumps(layout, ensure_ascii=False, indent=2).encode("utf-8") + b"\n",
            source=str(layout_path),
        )
        env_entry = payload_entry_from_file(env_example_path, "config/pi-hud.env.example")
        preview_entry = payload_entry_from_file(preview_path, "preview/layout-preview.png")
        vehicle_entries = vehicle_profile_payload_entries(layout, vehicle_profile_dirs)
        asset_entries = asset_payload_entries(warning_assets_dir, nav_assets_dir)

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
