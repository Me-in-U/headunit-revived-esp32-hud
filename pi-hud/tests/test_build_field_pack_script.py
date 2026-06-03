from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path


def load_build_field_pack_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "build-field-pack.py"
    spec = importlib.util.spec_from_file_location("build_field_pack", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load build-field-pack.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BuildFieldPackScriptTest(unittest.TestCase):
    def test_parser_defaults_to_repo_layout_profiles_and_env_example(self) -> None:
        module = load_build_field_pack_module()

        args = module.build_parser().parse_args(["--output", "field-pack.zip"])

        self.assertEqual("layouts/avante_hd_2010_default.json", args.layout)
        self.assertEqual("vehicles", args.vehicles_dir)
        self.assertEqual("pi-hud/config/pi-hud.env.example", args.env_example)
        self.assertEqual("pi-hud/assets/nav-icons", args.nav_assets_dir)
        self.assertTrue(args.require_handoff)

    def test_script_writes_transfer_zip_with_manifest_hashes(self) -> None:
        module = load_build_field_pack_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "headunit-pi-field-pack.zip"

            exit_code = module.main(["--output", str(output)])

            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
                layout_bytes = archive.read("layouts/avante_hd_2010_default.json")
                env_bytes = archive.read("config/pi-hud.env.example")
                preview_bytes = archive.read("preview/layout-preview.png")
                warning_icon_bytes = archive.read("pi-hud/assets/warning-icons/door_open.png")
                nav_icon_bytes = archive.read("pi-hud/assets/nav-icons/turn_right.png")
                readme = archive.read("README-pi-field-pack.txt").decode("utf-8")

        self.assertEqual(0, exit_code)
        self.assertIn("layouts/avante_hd_2010_default.json", names)
        self.assertIn("vehicles/avante_hd_2010_1_6_at.json", names)
        self.assertIn("config/pi-hud.env.example", names)
        self.assertIn("pi-hud/assets/warning-icons/door_open.png", names)
        self.assertIn("pi-hud/assets/nav-icons/turn_right.png", names)
        self.assertIn("preview/layout-preview.png", names)
        self.assertIn("README-pi-field-pack.txt", names)

        self.assertEqual("headunit-pi-field-pack", manifest["kind"])
        self.assertEqual(1, manifest["schema_version"])
        self.assertEqual("avante_hd_2010_1_6_at", manifest["selected_vehicle"])
        self.assertTrue(manifest["layout"]["require_handoff"])
        self.assertEqual("layouts/avante_hd_2010_default.json", manifest["layout"]["path"])
        self.assertEqual(hashlib.sha256(layout_bytes).hexdigest(), manifest["layout"]["sha256"])
        self.assertEqual(hashlib.sha256(env_bytes).hexdigest(), manifest["env_example"]["sha256"])
        warning_icon_entry = next(item for item in manifest["assets"] if item["path"] == "pi-hud/assets/warning-icons/door_open.png")
        self.assertEqual(hashlib.sha256(warning_icon_bytes).hexdigest(), warning_icon_entry["sha256"])
        nav_icon_entry = next(item for item in manifest["assets"] if item["path"] == "pi-hud/assets/nav-icons/turn_right.png")
        self.assertEqual(hashlib.sha256(nav_icon_bytes).hexdigest(), nav_icon_entry["sha256"])
        self.assertEqual("preview/layout-preview.png", manifest["preview"]["path"])
        self.assertEqual([1920, 480], manifest["preview"]["render_size"])
        self.assertEqual(hashlib.sha256(preview_bytes).hexdigest(), manifest["preview"]["sha256"])
        self.assertTrue(preview_bytes.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertTrue(any(item["path"] == "vehicles/avante_hd_2010_1_6_at.json" for item in manifest["vehicles"]))
        self.assertIn("acceptance-check.py --probe-display --probe-inputs --json", readme)
        self.assertIn("/opt/headunit-pi-hud/vehicle-baseline/acceptance-check.json", readme)


if __name__ == "__main__":
    unittest.main()
