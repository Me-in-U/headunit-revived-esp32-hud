from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from hud_pi.field_pack_manifest_paths import relative_source, target_path, validate_archive_path


class FieldPackManifestPathsTest(unittest.TestCase):
    def test_archive_path_helpers_preserve_safe_target_rules(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app_dir = Path(temp_dir) / "app"

            self.assertIsNone(validate_archive_path("layouts/test.json"))
            self.assertEqual(app_dir / "layouts" / "test.json", target_path(app_dir, "layouts/test.json", required_prefix="layouts"))
            with self.assertRaisesRegex(ValueError, "unsafe archive path"):
                validate_archive_path("../layouts/test.json")
            with self.assertRaisesRegex(ValueError, "archive path must use forward slashes"):
                validate_archive_path("layouts\\test.json")
            with self.assertRaisesRegex(ValueError, "config/pi-hud.env.example must be under layouts/"):
                target_path(app_dir, "config/pi-hud.env.example", required_prefix="layouts")

    def test_relative_source_uses_repo_relative_path_when_possible(self) -> None:
        repo_root = Path("repo")

        self.assertEqual("layouts/test.json", relative_source(repo_root / "layouts" / "test.json", repo_root))
        self.assertEqual("outside.json", relative_source(Path("outside.json"), repo_root))
        self.assertEqual("outside.json", relative_source(Path("outside.json"), None))


if __name__ == "__main__":
    unittest.main()
