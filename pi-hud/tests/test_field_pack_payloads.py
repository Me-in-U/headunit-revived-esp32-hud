from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from hud_pi.field_pack_payloads import (
    archive_asset_path,
    archive_layout_path,
    payload_entry_from_file,
    readme_text,
)


class FieldPackPayloadsTest(unittest.TestCase):
    def test_payload_helpers_preserve_archive_paths_sources_and_readme_contract(self) -> None:
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

        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "payload.txt"
            source.write_text("payload", encoding="utf-8")

            entry = payload_entry_from_file(source, "config/payload.txt")

        self.assertEqual("config/payload.txt", entry.path)
        self.assertEqual(b"payload", entry.payload)
        self.assertEqual(str(source), entry.source)


if __name__ == "__main__":
    unittest.main()
