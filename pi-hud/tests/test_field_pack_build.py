from __future__ import annotations

import unittest
from pathlib import Path

from hud_pi.field_pack_build import archive_asset_path, archive_layout_path, readme_text


class FieldPackBuildTest(unittest.TestCase):
    def test_build_module_exposes_archive_paths_and_readme_contract(self) -> None:
        repo_root = Path("repo")

        self.assertEqual(
            "layouts/cluster/default.json",
            archive_layout_path(repo_root / "layouts" / "cluster" / "default.json", repo_root),
        )
        self.assertEqual(
            "layouts/outside.json",
            archive_layout_path(Path("outside.json"), repo_root),
        )
        self.assertEqual(
            "pi-hud/assets/warning-icons/door_open.png",
            archive_asset_path(Path("assets/door_open.png"), Path("assets"), "pi-hud/assets/warning-icons"),
        )
        self.assertIn("layouts/cluster/default.json", readme_text("layouts/cluster/default.json"))


if __name__ == "__main__":
    unittest.main()
