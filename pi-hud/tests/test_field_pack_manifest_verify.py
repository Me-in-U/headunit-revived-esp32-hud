from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from hud_pi.field_pack_manifest_model import FIELD_PACK_KIND, FIELD_PACK_SCHEMA_VERSION
from hud_pi.field_pack_manifest_verify import load_manifest, manifest_entries, verify_payloads


class FieldPackManifestVerifyTest(unittest.TestCase):
    def test_manifest_verify_helpers_preserve_load_entry_and_hash_rules(self) -> None:
        layout_payload = b"{}"
        env_payload = b"ENV=1\n"
        manifest = {
            "kind": FIELD_PACK_KIND,
            "schema_version": FIELD_PACK_SCHEMA_VERSION,
            "layout": {"path": "layouts/test.json", "sha256": hashlib.sha256(layout_payload).hexdigest()},
            "vehicles": [],
            "assets": [],
            "env_example": {"path": "config/pi-hud.env.example", "sha256": hashlib.sha256(env_payload).hexdigest()},
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            package = Path(temp_dir) / "pack.zip"
            with zipfile.ZipFile(package, "w") as archive:
                archive.writestr("manifest.json", json.dumps(manifest))
                archive.writestr("layouts/test.json", layout_payload)
                archive.writestr("config/pi-hud.env.example", env_payload)

            with zipfile.ZipFile(package) as archive:
                loaded = load_manifest(archive)
                layout_entry, vehicle_entries, asset_entries, env_entry = manifest_entries(loaded)
                payloads = verify_payloads(archive, [layout_entry, env_entry])

        self.assertEqual([], vehicle_entries)
        self.assertEqual([], asset_entries)
        self.assertEqual(layout_payload, payloads["layouts/test.json"])


if __name__ == "__main__":
    unittest.main()
