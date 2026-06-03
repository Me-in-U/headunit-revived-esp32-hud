from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

from hud_pi.field_pack_manifest import PayloadEntry
from hud_pi.field_pack_payloads import readme_text


def write_field_pack(
    output_path: Path,
    layout_entry: PayloadEntry,
    env_entry: PayloadEntry,
    preview_entry: PayloadEntry,
    vehicle_entries: list[PayloadEntry],
    asset_entries: list[PayloadEntry],
    manifest: dict[str, Any],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for entry in [layout_entry, *vehicle_entries, *asset_entries, env_entry, preview_entry]:
            archive.writestr(entry.path, entry.payload)
        archive.writestr("README-pi-field-pack.txt", readme_text(layout_entry.path))
        archive.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
