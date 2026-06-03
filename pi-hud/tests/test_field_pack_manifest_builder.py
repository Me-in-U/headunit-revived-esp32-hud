from __future__ import annotations

import hashlib
import unittest
from types import SimpleNamespace

from hud_pi.field_pack_manifest_builder import build_manifest, manifest_entry
from hud_pi.field_pack_manifest_model import PayloadEntry


class FieldPackManifestBuilderTest(unittest.TestCase):
    def test_build_manifest_preserves_transfer_manifest_shape(self) -> None:
        layout_entry = PayloadEntry("layouts/test.json", b"{}", source="layout.json")
        env_entry = PayloadEntry("config/pi-hud.env.example", b"ENV=1\n")
        preview_entry = PayloadEntry("preview/layout-preview.png", b"png")
        vehicle_entry = PayloadEntry("vehicles/car.json", b'{"id":"car"}')
        asset_entry = PayloadEntry("pi-hud/assets/nav-icons/turn.png", b"asset")
        verification = SimpleNamespace(render_size=(1920, 480), non_background_pixels=123)

        manifest = build_manifest(
            layout={"selected_vehicle": "car"},
            layout_entry=layout_entry,
            env_entry=env_entry,
            preview_entry=preview_entry,
            vehicle_entries=[vehicle_entry],
            asset_entries=[asset_entry],
            verification=verification,
            require_handoff=True,
        )

        self.assertEqual("headunit-pi-field-pack", manifest["kind"])
        self.assertEqual("car", manifest["selected_vehicle"])
        self.assertEqual([1920, 480], manifest["layout"]["render_size"])
        self.assertEqual(123, manifest["layout"]["non_background_pixels"])
        self.assertTrue(manifest["layout"]["require_handoff"])
        self.assertEqual("/opt/headunit-pi-hud/layouts/test.json", manifest["install_targets"]["layout"])
        self.assertEqual(hashlib.sha256(b"{}").hexdigest(), manifest["layout"]["sha256"])
        self.assertEqual("layout.json", manifest_entry(layout_entry)["source"])


if __name__ == "__main__":
    unittest.main()
