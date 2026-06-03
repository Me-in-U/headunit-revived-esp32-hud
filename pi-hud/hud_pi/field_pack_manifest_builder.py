from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from hud_pi.field_pack_manifest_model import FIELD_PACK_KIND, FIELD_PACK_SCHEMA_VERSION, PayloadEntry


def build_manifest(
    *,
    layout: dict[str, Any],
    layout_entry: PayloadEntry,
    env_entry: PayloadEntry,
    preview_entry: PayloadEntry,
    vehicle_entries: list[PayloadEntry],
    asset_entries: list[PayloadEntry],
    verification: Any,
    require_handoff: bool,
) -> dict[str, Any]:
    return {
        "kind": FIELD_PACK_KIND,
        "schema_version": FIELD_PACK_SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "selected_vehicle": str(layout.get("selected_vehicle", "")).strip(),
        "layout": {
            **manifest_entry(layout_entry),
            "render_size": [verification.render_size[0], verification.render_size[1]],
            "non_background_pixels": verification.non_background_pixels,
            "require_handoff": bool(require_handoff),
        },
        "preview": {
            **manifest_entry(preview_entry),
            "render_size": [verification.render_size[0], verification.render_size[1]],
            "non_background_pixels": verification.non_background_pixels,
        },
        "vehicles": [manifest_entry(entry) for entry in vehicle_entries],
        "assets": [manifest_entry(entry) for entry in asset_entries],
        "env_example": manifest_entry(env_entry),
        "install_targets": {
            "app_dir": "/opt/headunit-pi-hud",
            "env_file": "/etc/headunit-pi-hud.env",
            "layout": f"/opt/headunit-pi-hud/{layout_entry.path}",
        },
    }


def manifest_entry(entry: PayloadEntry) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": entry.path,
        "size": len(entry.payload),
        "sha256": hashlib.sha256(entry.payload).hexdigest(),
    }
    if entry.source:
        result["source"] = entry.source
    return result
