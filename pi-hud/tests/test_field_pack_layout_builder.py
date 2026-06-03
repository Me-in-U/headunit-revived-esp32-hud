from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from hud_pi.field_pack_layout_builder import build_field_pack_from_layout


class FieldPackLayoutBuilderTest(unittest.TestCase):
    def test_layout_builder_preserves_env_example_validation_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            with self.assertRaisesRegex(ValueError, "Pi HUD env example does not exist:"):
                build_field_pack_from_layout(
                    layout={"canvas": {"width": 1920, "height": 480}, "elements": []},
                    layout_path=root / "layout.json",
                    vehicle_profile_dirs=[],
                    env_example_path=root / "missing.env.example",
                    warning_assets_dir=root,
                    nav_assets_dir=root,
                    output_path=root / "pack.zip",
                    width=1920,
                    height=480,
                )


if __name__ == "__main__":
    unittest.main()
