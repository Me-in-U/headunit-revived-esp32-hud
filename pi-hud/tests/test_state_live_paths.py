from __future__ import annotations

import unittest

from hud_pi.state_live_paths import live_paths_for_source, set_path_to_none


class StateLivePathsTest(unittest.TestCase):
    def test_live_paths_for_source_tracks_only_runtime_owned_fields(self) -> None:
        obd_update = {"vehicle": {"speed_kmh": 72, "rpm": 2100, "obd_state": "live"}, "debug": {"obd_request": "010C"}}
        can_update = {"vehicle": {"can_state": "live", "gear_actual": "D"}, "debug": {"last_can_id": "0x316"}}
        bridge_speed_update = {"vehicle": {"speed_kmh_backup": 57, "source": "android"}}

        self.assertEqual(["vehicle.speed_kmh", "vehicle.rpm"], live_paths_for_source("obd", obd_update))
        self.assertEqual(["vehicle.gear_actual"], live_paths_for_source("can", can_update))
        self.assertEqual(["vehicle.speed_kmh_backup"], live_paths_for_source("bridge_speed", bridge_speed_update))
        self.assertEqual([], live_paths_for_source("dummy", {"vehicle": {"speed_kmh": 42}}))

    def test_set_path_to_none_only_clears_existing_leaf_paths(self) -> None:
        values = {"vehicle": {"speed_kmh": 72, "nested": {"value": 1}}}

        set_path_to_none(values, "vehicle.speed_kmh")
        set_path_to_none(values, "vehicle.missing")
        set_path_to_none(values, "missing.path")

        self.assertIsNone(values["vehicle"]["speed_kmh"])
        self.assertEqual({"value": 1}, values["vehicle"]["nested"])


if __name__ == "__main__":
    unittest.main()
