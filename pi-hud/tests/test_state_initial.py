from __future__ import annotations

import unittest

from hud_pi.state_initial import build_initial_state, initial_vehicle_status_update


class StateInitialTest(unittest.TestCase):
    def test_initial_state_helpers_preserve_vehicle_status_and_dummy_clearing(self) -> None:
        self.assertEqual(
            {
                "vehicle": {
                    "source": "pi-local",
                    "obd_state": "configured",
                    "can_state": "configured",
                }
            },
            initial_vehicle_status_update(obd_configured=True, can_configured=True, dummy_enabled=False),
        )

        state = build_initial_state(
            {
                "dummy_data": {
                    "vehicle": {"source": "dummy", "speed_kmh": 42, "rpm": 1850},
                    "nav": {"connected": True, "instruction": "Turn right"},
                }
            },
            obd_configured=True,
            can_configured=True,
            dummy_enabled=False,
        )

        self.assertEqual("pi-local", state.resolve("vehicle.source"))
        self.assertIsNone(state.resolve("vehicle.speed_kmh", None))
        self.assertIsNone(state.resolve("vehicle.rpm", None))
        self.assertFalse(state.resolve("nav.connected"))
        self.assertEqual("", state.resolve("nav.instruction"))


if __name__ == "__main__":
    unittest.main()
