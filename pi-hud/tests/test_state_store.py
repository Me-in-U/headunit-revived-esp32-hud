from __future__ import annotations

import time
import unittest

from hud_pi.state_store import HudState


class StateStoreTest(unittest.TestCase):
    def test_state_store_preserves_merge_resolve_and_dummy_fill_rules(self) -> None:
        state = HudState({"vehicle": {"source": "pi-obd", "speed_kmh": 72, "rpm": 2400, "atf_c": None}})

        state.merge("dummy", {"vehicle": {"source": "dummy", "speed_kmh": 42, "rpm": 1850, "atf_c": 84}})

        self.assertEqual("pi-obd", state.resolve("vehicle.source"))
        self.assertEqual(72, state.resolve("vehicle.speed_kmh"))
        self.assertEqual(2400, state.resolve("vehicle.rpm"))
        self.assertEqual(84, state.resolve("vehicle.atf_c"))
        self.assertEqual("--", state.resolve("vehicle.missing"))

    def test_state_store_preserves_owned_live_path_stale_clearing(self) -> None:
        state = HudState({"vehicle": {"can_state": "live", "gear_actual": "D", "pedal_percent": 40}})
        state.merge("can", {"vehicle": {"can_state": "live", "gear_actual": "D", "pedal_percent": 40}})
        state.updated_at["can"] = time.monotonic() - 3

        state.mark_stale_sources(stale_after_ms=2500)

        self.assertEqual("stale", state.resolve("vehicle.can_state"))
        self.assertIsNone(state.resolve("vehicle.gear_actual", None))
        self.assertIsNone(state.resolve("vehicle.pedal_percent", None))


if __name__ == "__main__":
    unittest.main()
