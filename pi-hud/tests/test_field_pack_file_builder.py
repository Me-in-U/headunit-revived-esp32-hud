from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from hud_pi.field_pack_file_builder import build_field_pack_from_file


class FieldPackFileBuilderTest(unittest.TestCase):
    def test_file_builder_preserves_layout_path_validation_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            with self.assertRaisesRegex(ValueError, "layout does not exist:"):
                build_field_pack_from_file(
                    layout_path=root / "missing.json",
                    vehicles_dir=root,
                    env_example_path=root / "env.example",
                    warning_assets_dir=root,
                    nav_assets_dir=root,
                    output_path=root / "pack.zip",
                    repo_root=root,
                )


if __name__ == "__main__":
    unittest.main()
