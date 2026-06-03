from __future__ import annotations

import importlib.util
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path


def load_script(script_name: str, module_name: str):
    script_path = Path(__file__).resolve().parents[1] / "scripts" / script_name
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {script_name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ApplyFieldPackScriptTest(unittest.TestCase):
    def test_parser_defaults_to_installed_app_and_preserves_existing_env(self) -> None:
        module = load_script("apply-field-pack.py", "apply_field_pack")

        args = module.build_parser().parse_args(["headunit-pi-field-pack.zip"])

        self.assertEqual("headunit-pi-field-pack.zip", args.package)
        self.assertEqual("/opt/headunit-pi-hud", args.app_dir)
        self.assertEqual("/etc/headunit-pi-hud.env", args.env_file)
        self.assertFalse(args.overwrite_env)

    def test_script_verifies_hashes_and_applies_layout_and_vehicles_without_overwriting_env(self) -> None:
        build_module = load_script("build-field-pack.py", "build_field_pack_for_apply_test")
        apply_module = load_script("apply-field-pack.py", "apply_field_pack")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package = temp_path / "headunit-pi-field-pack.zip"
            app_dir = temp_path / "app"
            env_file = temp_path / "headunit-pi-hud.env"
            env_file.write_text("HEADUNIT_HUD_OBD_PORT=/dev/rfcomm0\nUSER_CUSTOM=1\n", encoding="utf-8")

            self.assertEqual(0, build_module.main(["--output", str(package)]))
            exit_code = apply_module.main([str(package), "--app-dir", str(app_dir), "--env-file", str(env_file)])

            with zipfile.ZipFile(package) as archive:
                layout_bytes = archive.read("layouts/avante_hd_2010_default.json")
                vehicle_bytes = archive.read("vehicles/avante_hd_2010_1_6_at.json")
                warning_icon_bytes = archive.read("pi-hud/assets/warning-icons/door_open.png")
                nav_icon_bytes = archive.read("pi-hud/assets/nav-icons/turn_right.png")

            self.assertEqual(0, exit_code)
            self.assertEqual(layout_bytes, (app_dir / "layouts" / "avante_hd_2010_default.json").read_bytes())
            self.assertEqual(vehicle_bytes, (app_dir / "vehicles" / "avante_hd_2010_1_6_at.json").read_bytes())
            self.assertEqual(warning_icon_bytes, (app_dir / "pi-hud" / "assets" / "warning-icons" / "door_open.png").read_bytes())
            self.assertEqual(nav_icon_bytes, (app_dir / "pi-hud" / "assets" / "nav-icons" / "turn_right.png").read_bytes())
            self.assertEqual("HEADUNIT_HUD_OBD_PORT=/dev/rfcomm0\nUSER_CUSTOM=1\n", env_file.read_text(encoding="utf-8"))

    def test_script_rejects_tampered_manifest_hash_before_writing_files(self) -> None:
        module = load_script("apply-field-pack.py", "apply_field_pack")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package = temp_path / "tampered.zip"
            app_dir = temp_path / "app"
            manifest = {
                "kind": "headunit-pi-field-pack",
                "schema_version": 1,
                "layout": {"path": "layouts/avante_hd_2010_default.json", "sha256": "0" * 64},
                "vehicles": [],
                "env_example": {"path": "config/pi-hud.env.example", "sha256": "1" * 64},
            }
            with zipfile.ZipFile(package, "w") as archive:
                archive.writestr("manifest.json", json.dumps(manifest))
                archive.writestr("layouts/avante_hd_2010_default.json", "{}")
                archive.writestr("config/pi-hud.env.example", "HEADUNIT_HUD_DUMMY=0\n")

            exit_code = module.main([str(package), "--app-dir", str(app_dir), "--env-file", str(temp_path / "env")])

            self.assertEqual(1, exit_code)
            self.assertFalse((app_dir / "layouts" / "avante_hd_2010_default.json").exists())

    def test_script_rejects_layout_that_hashes_but_does_not_render_before_writing_files(self) -> None:
        module = load_script("apply-field-pack.py", "apply_field_pack")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package = temp_path / "blank-layout.zip"
            app_dir = temp_path / "app"
            layout_payload = b"{}"
            env_payload = b"HEADUNIT_HUD_DUMMY=0\n"
            manifest = {
                "kind": "headunit-pi-field-pack",
                "schema_version": 1,
                "layout": {
                    "path": "layouts/avante_hd_2010_default.json",
                    "sha256": hashlib.sha256(layout_payload).hexdigest(),
                    "render_size": [1920, 480],
                    "require_handoff": False,
                },
                "vehicles": [],
                "env_example": {
                    "path": "config/pi-hud.env.example",
                    "sha256": hashlib.sha256(env_payload).hexdigest(),
                },
            }
            with zipfile.ZipFile(package, "w") as archive:
                archive.writestr("manifest.json", json.dumps(manifest))
                archive.writestr("layouts/avante_hd_2010_default.json", layout_payload)
                archive.writestr("config/pi-hud.env.example", env_payload)

            exit_code = module.main([str(package), "--app-dir", str(app_dir), "--env-file", str(temp_path / "env")])

            self.assertEqual(1, exit_code)
            self.assertFalse((app_dir / "layouts" / "avante_hd_2010_default.json").exists())


if __name__ == "__main__":
    unittest.main()
