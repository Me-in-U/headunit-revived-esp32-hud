from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from hud_pi.field_pack_manifest import (
    FIELD_PACK_KIND,
    FIELD_PACK_SCHEMA_VERSION,
    load_manifest,
    manifest_entries,
    target_path,
    validate_archive_path,
    verify_payloads,
)


class FieldPackManifestTest(unittest.TestCase):
    def test_manifest_module_validates_payload_hashes_and_safe_targets(self) -> None:
        layout_payload = b'{"canvas":{"width":1920,"height":480},"elements":[]}'
        env_payload = b"HEADUNIT_HUD_DUMMY=0\n"
        manifest = {
            "kind": FIELD_PACK_KIND,
            "schema_version": FIELD_PACK_SCHEMA_VERSION,
            "layout": {"path": "layouts/test.json", "sha256": hashlib.sha256(layout_payload).hexdigest()},
            "vehicles": [],
            "assets": [],
            "env_example": {"path": "config/pi-hud.env.example", "sha256": hashlib.sha256(env_payload).hexdigest()},
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            package = Path(temp_dir) / "field-pack.zip"
            app_dir = Path(temp_dir) / "app"
            with zipfile.ZipFile(package, "w") as archive:
                archive.writestr("manifest.json", json.dumps(manifest))
                archive.writestr("layouts/test.json", layout_payload)
                archive.writestr("config/pi-hud.env.example", env_payload)

            with zipfile.ZipFile(package) as archive:
                loaded = load_manifest(archive)
                layout_entry, _vehicle_entries, _asset_entries, env_entry = manifest_entries(loaded)
                payloads = verify_payloads(archive, [layout_entry, env_entry])

        self.assertEqual(layout_payload, payloads["layouts/test.json"])
        self.assertEqual(app_dir / "layouts" / "test.json", target_path(app_dir, "layouts/test.json", required_prefix="layouts"))
        with self.assertRaises(ValueError):
            validate_archive_path("../layouts/test.json")
        with self.assertRaises(ValueError):
            target_path(app_dir, "config/pi-hud.env.example", required_prefix="layouts")
        with self.assertRaises(ValueError):
            target_path(app_dir, "layouts/../escaped.json", required_prefix="layouts")


if __name__ == "__main__":
    unittest.main()
