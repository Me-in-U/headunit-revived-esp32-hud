from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from hud_pi.field_pack import (
    build_field_pack_from_file,
    build_field_pack_from_layout,
    load_manifest,
    manifest_entries,
    target_path,
    validate_archive_path,
    verify_payloads,
)
from hud_pi.layout import load_layout, normalize_layout_for_save
from hud_pi.layout_verifier import build_layout_handoff, verify_layout


ROOT_DIR = Path(__file__).resolve().parents[2]


class FieldPackTest(unittest.TestCase):
    def test_file_builder_records_repo_relative_sources_in_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "headunit-pi-field-pack.zip"

            build_field_pack_from_file(
                layout_path=ROOT_DIR / "layouts" / "avante_hd_2010_default.json",
                vehicles_dir=ROOT_DIR / "vehicles",
                env_example_path=ROOT_DIR / "pi-hud" / "config" / "pi-hud.env.example",
                warning_assets_dir=ROOT_DIR / "pi-hud" / "assets" / "warning-icons",
                nav_assets_dir=ROOT_DIR / "pi-hud" / "assets" / "nav-icons",
                output_path=output,
                repo_root=ROOT_DIR,
            )

            with zipfile.ZipFile(output) as archive:
                manifest = json.loads(archive.read("manifest.json").decode("utf-8"))

        self.assertEqual("layouts/avante_hd_2010_default.json", manifest["layout"]["source"])
        self.assertEqual("pi-hud/config/pi-hud.env.example", manifest["env_example"]["source"])

    def test_in_memory_layout_builder_writes_same_transfer_contract(self) -> None:
        layout_path = ROOT_DIR / "layouts" / "avante_hd_2010_default.json"
        layout = normalize_layout_for_save(load_layout(layout_path))
        canvas = layout["canvas"]
        verification = verify_layout(layout, width=canvas["width"], height=canvas["height"])
        self.assertTrue(verification.ok, verification.errors)
        layout["pi_hud_handoff"] = build_layout_handoff(
            layout,
            verification.render_size,
            verification.non_background_pixels,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "headunit-pi-field-pack.zip"

            result = build_field_pack_from_layout(
                layout=layout,
                layout_path=layout_path,
                vehicle_profile_dirs=[ROOT_DIR / "vehicles"],
                env_example_path=ROOT_DIR / "pi-hud" / "config" / "pi-hud.env.example",
                warning_assets_dir=ROOT_DIR / "pi-hud" / "assets" / "warning-icons",
                nav_assets_dir=ROOT_DIR / "pi-hud" / "assets" / "nav-icons",
                output_path=output,
                width=canvas["width"],
                height=canvas["height"],
                require_handoff=True,
            )

            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
                layout_bytes = archive.read("layouts/avante_hd_2010_default.json")
                preview_bytes = archive.read("preview/layout-preview.png")

        self.assertEqual(output, result.output)
        self.assertIn("layouts/avante_hd_2010_default.json", names)
        self.assertIn("vehicles/avante_hd_2010_1_6_at.json", names)
        self.assertIn("pi-hud/assets/warning-icons/door_open.png", names)
        self.assertIn("pi-hud/assets/nav-icons/turn_right.png", names)
        self.assertIn("README-pi-field-pack.txt", names)
        self.assertEqual("headunit-pi-field-pack", manifest["kind"])
        self.assertEqual("avante_hd_2010_1_6_at", manifest["selected_vehicle"])
        self.assertTrue(manifest["layout"]["require_handoff"])
        self.assertEqual(hashlib.sha256(layout_bytes).hexdigest(), manifest["layout"]["sha256"])
        self.assertEqual(hashlib.sha256(preview_bytes).hexdigest(), manifest["preview"]["sha256"])
        self.assertEqual([canvas["width"], canvas["height"]], manifest["preview"]["render_size"])

    def test_manifest_helpers_validate_archive_paths_hashes_and_install_targets(self) -> None:
        layout_payload = b'{"canvas":{"width":1920,"height":480},"elements":[]}'
        env_payload = b"HEADUNIT_HUD_DUMMY=0\n"
        layout_digest = hashlib.sha256(layout_payload).hexdigest()
        env_digest = hashlib.sha256(env_payload).hexdigest()
        manifest = {
            "kind": "headunit-pi-field-pack",
            "schema_version": 1,
            "layout": {"path": "layouts/test.json", "sha256": layout_digest},
            "vehicles": [],
            "assets": [],
            "env_example": {"path": "config/pi-hud.env.example", "sha256": env_digest},
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            package = Path(temp_dir) / "pack.zip"
            app_dir = Path(temp_dir) / "app"
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
        self.assertEqual(app_dir / "layouts" / "test.json", target_path(app_dir, "layouts/test.json", required_prefix="layouts"))
        with self.assertRaises(ValueError):
            validate_archive_path("../layouts/test.json")
        with self.assertRaises(ValueError):
            target_path(app_dir, "config/pi-hud.env.example", required_prefix="layouts")


if __name__ == "__main__":
    unittest.main()
