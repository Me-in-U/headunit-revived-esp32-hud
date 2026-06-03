from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from hud_pi.field_pack_requirements import require_directory, require_file
from hud_pi.field_pack_result import FieldPackResult


class FieldPackRequirementsTest(unittest.TestCase):
    def test_require_helpers_preserve_missing_path_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            existing_file = root / "layout.json"
            existing_dir = root / "vehicles"
            existing_file.write_text("{}", encoding="utf-8")
            existing_dir.mkdir()

            require_file(existing_file, "layout")
            require_directory(existing_dir, "vehicles dir")

            with self.assertRaisesRegex(ValueError, "layout does not exist:"):
                require_file(root / "missing.json", "layout")
            with self.assertRaisesRegex(ValueError, "vehicles dir does not exist:"):
                require_directory(root / "missing-dir", "vehicles dir")

    def test_field_pack_result_keeps_builder_return_contract(self) -> None:
        result = FieldPackResult(
            output=Path("pack.zip"),
            render_size=(1920, 480),
            non_background_pixels=123,
            manifest={"kind": "headunit-pi-field-pack"},
        )

        self.assertEqual(Path("pack.zip"), result.output)
        self.assertEqual((1920, 480), result.render_size)


if __name__ == "__main__":
    unittest.main()
