from __future__ import annotations

import unittest

from hud_pi.dummy_sources import DummyVehicleSource, dummy_vehicle_update


class DummySourcesTest(unittest.TestCase):
    def test_dummy_vehicle_update_contains_vehicle_and_warning_defaults(self) -> None:
        update = dummy_vehicle_update(elapsed=0.0)

        self.assertEqual("dummy", update["vehicle"]["source"])
        self.assertEqual("dummy", update["vehicle"]["obd_state"])
        self.assertEqual("dummy", update["vehicle"]["can_state"])
        self.assertEqual("D", update["vehicle"]["gear_range"])
        self.assertEqual(42, update["vehicle"]["speed_kmh"])
        self.assertEqual(2208, update["vehicle"]["rpm"])
        self.assertTrue(update["warnings"]["eco"])
        self.assertFalse(update["warnings"]["door_open"])

    def test_dummy_vehicle_source_uses_dummy_thread_name(self) -> None:
        source = DummyVehicleSource(lambda _source, _update: None)

        self.assertEqual("dummy-vehicle", source.name)


if __name__ == "__main__":
    unittest.main()
