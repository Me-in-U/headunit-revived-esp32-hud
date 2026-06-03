from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from hud_pi.field_pack_apply import apply_field_pack_package
from hud_pi.field_pack_manifest import FIELD_PACK_KIND, FIELD_PACK_SCHEMA_VERSION


class FieldPackApplyTest(unittest.TestCase):
    def test_apply_package_stages_layout_vehicle_assets_and_preserves_existing_env(self) -> None:
        layout_payload = b'{"canvas":{"width":1920,"height":480},"elements":[]}\n'
        vehicle_payload = b'{"id":"demo"}\n'
        asset_payload = b"\x89PNG\r\n"
        env_payload = b"HEADUNIT_HUD_DUMMY=0\n"
        manifest = {
            "kind": FIELD_PACK_KIND,
            "schema_version": FIELD_PACK_SCHEMA_VERSION,
            "layout": {
                "path": "layouts/demo.json",
                "sha256": hashlib.sha256(layout_payload).hexdigest(),
                "render_size": [1920, 480],
            },
            "vehicles": [
                {"path": "vehicles/demo.json", "sha256": hashlib.sha256(vehicle_payload).hexdigest()},
            ],
            "assets": [
                {"path": "pi-hud/assets/warning-icons/demo.png", "sha256": hashlib.sha256(asset_payload).hexdigest()},
            ],
            "env_example": {
                "path": "config/pi-hud.env.example",
                "sha256": hashlib.sha256(env_payload).hexdigest(),
            },
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            package = root / "field-pack.zip"
            app_dir = root / "app"
            env_file = root / "pi-hud.env"
            env_file.write_bytes(b"EXISTING=1\n")
            with zipfile.ZipFile(package, "w") as archive:
                archive.writestr("manifest.json", json.dumps(manifest))
                archive.writestr("layouts/demo.json", layout_payload)
                archive.writestr("vehicles/demo.json", vehicle_payload)
                archive.writestr("pi-hud/assets/warning-icons/demo.png", asset_payload)
                archive.writestr("config/pi-hud.env.example", env_payload)

            with patch(
                "hud_pi.field_pack_apply.verify_layout_file",
                return_value=SimpleNamespace(ok=True, errors=[]),
            ):
                result = apply_field_pack_package(
                    package_path=package,
                    app_dir=app_dir,
                    env_file=env_file,
                    overwrite_env=False,
                )

            self.assertEqual(layout_payload, (app_dir / "layouts" / "demo.json").read_bytes())
            self.assertEqual(vehicle_payload, (app_dir / "vehicles" / "demo.json").read_bytes())
            self.assertEqual(asset_payload, (app_dir / "pi-hud" / "assets" / "warning-icons" / "demo.png").read_bytes())
            self.assertEqual(b"EXISTING=1\n", env_file.read_bytes())

        self.assertFalse(result.env_written)
        self.assertEqual(app_dir / "layouts" / "demo.json", result.layout)
        self.assertEqual([app_dir / "vehicles" / "demo.json"], result.vehicles)
        self.assertEqual([app_dir / "pi-hud" / "assets" / "warning-icons" / "demo.png"], result.assets)


if __name__ == "__main__":
    unittest.main()
