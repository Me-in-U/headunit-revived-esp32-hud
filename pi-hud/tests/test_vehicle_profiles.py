from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from hud_pi.layout import load_layout
from hud_pi.vehicle_profiles import load_vehicle_profiles, upsert_vehicle_profile


class VehicleProfilesTest(unittest.TestCase):
    def test_load_vehicle_profiles_reads_json_files_from_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            (directory / "b.json").write_text(
                json.dumps({"id": "vehicle_b", "label": "Vehicle B", "confirmed": {}}),
                encoding="utf-8",
            )
            (directory / "a.json").write_text(
                json.dumps({"id": "vehicle_a", "label": "Vehicle A", "confirmed": {}}),
                encoding="utf-8",
            )

            profiles = load_vehicle_profiles([directory])

            self.assertEqual(["vehicle_a", "vehicle_b"], [profile["id"] for profile in profiles])

    def test_load_vehicle_profiles_rejects_missing_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            (directory / "broken.json").write_text(json.dumps({"label": "Broken"}), encoding="utf-8")

            with self.assertRaises(ValueError):
                load_vehicle_profiles([directory])

    def test_upsert_vehicle_profile_embeds_profile_and_selects_vehicle(self) -> None:
        layout = load_layout("layouts/avante_hd_2010_default.json")
        profile = {
            "id": "test_vehicle",
            "label": "Test Vehicle",
            "description_ko": "테스트 차량",
            "confirmed": {"abs": None},
        }

        upsert_vehicle_profile(layout, profile, select=True)

        self.assertEqual("test_vehicle", layout["selected_vehicle"])
        self.assertIn(profile, layout["vehicles"])

    def test_default_avante_profile_file_matches_layout_vehicle(self) -> None:
        layout = load_layout("layouts/avante_hd_2010_default.json")
        profile = load_vehicle_profiles(["vehicles"])[0]

        self.assertEqual(layout["vehicles"][0], profile)


if __name__ == "__main__":
    unittest.main()
