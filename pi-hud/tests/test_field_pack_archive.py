from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from hud_pi.field_pack_archive import write_field_pack
from hud_pi.field_pack_manifest import PayloadEntry


class FieldPackArchiveTest(unittest.TestCase):
    def test_write_field_pack_preserves_zip_contract_entries(self) -> None:
        layout = PayloadEntry("layouts/test.json", b"{}")
        env = PayloadEntry("config/pi-hud.env.example", b"HEADUNIT_HUD_DUMMY=0\n")
        preview = PayloadEntry("preview/layout-preview.png", b"png")
        vehicle = PayloadEntry("vehicles/car.json", b'{"id":"car"}')
        asset = PayloadEntry("pi-hud/assets/warning-icons/door_open.png", b"asset")
        manifest = {"kind": "headunit-pi-field-pack", "layout": {"path": layout.path}}

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "pack.zip"
            write_field_pack(output, layout, env, preview, [vehicle], [asset], manifest)

            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                readme = archive.read("README-pi-field-pack.txt").decode("utf-8")
                loaded_manifest = json.loads(archive.read("manifest.json").decode("utf-8"))

        self.assertIn("layouts/test.json", names)
        self.assertIn("vehicles/car.json", names)
        self.assertIn("pi-hud/assets/warning-icons/door_open.png", names)
        self.assertIn("config/pi-hud.env.example", names)
        self.assertIn("preview/layout-preview.png", names)
        self.assertIn("layouts/test.json", readme)
        self.assertEqual(manifest, loaded_manifest)


if __name__ == "__main__":
    unittest.main()
