from __future__ import annotations

import unittest

from hud_pi.state_packets import inactive_navigation_update, normalize_packet


class StatePacketsTest(unittest.TestCase):
    def test_normalize_navigation_speed_and_inactive_packets(self) -> None:
        nav_source, nav_update = normalize_packet(
            {
                "distance_meters": 300,
                "time_seconds": 25,
                "road": "Gangnam-daero",
                "action_text": "Turn right",
                "turn_side": 2,
                "next_event_type": 4,
            }
        )
        speed_source, speed_update = normalize_packet({"type": "speed", "speed_kmh": 57})
        inactive_source, inactive_update = normalize_packet({"type": "navigation", "active": False})

        self.assertEqual("bridge_nav", nav_source)
        self.assertEqual("Turn right", nav_update["nav"]["instruction"])
        self.assertEqual(4, nav_update["nav"]["event_type"])
        self.assertEqual(("bridge_speed", {"vehicle": {"speed_kmh_backup": 57}}), (speed_source, speed_update))
        self.assertEqual("bridge_nav", inactive_source)
        self.assertEqual(inactive_navigation_update(), inactive_update)

    def test_normalize_diagnostic_packets_require_explicit_opt_in(self) -> None:
        dtc_packet = {"type": "dtc_snapshot", "stored": ["P0133"], "pending": ["P0A0F"], "permanent": []}
        debug_packet = {"type": "vehicle_debug", "can_frame_count": 7, "last_can_id": "0x316"}

        self.assertEqual(("ignored", {}), normalize_packet(dtc_packet))
        self.assertEqual(("ignored", {}), normalize_packet(debug_packet))
        self.assertEqual(
            ("dtc", {"dtc": {"stored": ["P0133"], "pending": ["P0A0F"], "permanent": [], "count": 2}}),
            normalize_packet(dtc_packet, allow_diagnostic_packets=True),
        )
        debug_source, debug_update = normalize_packet(debug_packet, allow_diagnostic_packets=True)
        self.assertEqual("debug", debug_source)
        self.assertEqual(7, debug_update["debug"]["can_frame_count"])


if __name__ == "__main__":
    unittest.main()
