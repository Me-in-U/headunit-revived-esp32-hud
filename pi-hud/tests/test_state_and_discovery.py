from __future__ import annotations

import json
import time
import unittest

from hud_pi import state as state_module
from hud_pi.discovery import DEVICE_KIND_PI_HUD, build_discovery_hello, parse_discovery_probe
from hud_pi.state import HudState, initial_vehicle_status_update, normalize_packet


class StateAndDiscoveryTest(unittest.TestCase):
    def test_android_navigation_packet_only_updates_nav(self) -> None:
        source, update = normalize_packet(
            {
                "distance_meters": 300,
                "time_seconds": 25,
                "road": "Gangnam-daero",
                "action_text": "Turn right",
                "turn_side": 2,
                "event_type": 4,
            }
        )

        self.assertEqual("bridge_nav", source)
        self.assertIn("nav", update)
        self.assertNotIn("vehicle", update)
        self.assertEqual("Turn right", update["nav"]["instruction"])

    def test_android_speed_packet_is_backup_only(self) -> None:
        source, update = normalize_packet({"type": "speed", "speed_kmh": 57})

        self.assertEqual("bridge_speed", source)
        self.assertEqual({"vehicle": {"speed_kmh_backup": 57}}, update)

    def test_android_backup_speed_does_not_keep_navigation_fresh(self) -> None:
        state = HudState({"nav": {"connected": True}, "vehicle": {"speed_kmh_backup": 41}})
        state.merge("bridge_nav", {"nav": {"connected": True}})
        state.updated_at["bridge_nav"] = time.monotonic() - 3

        state.merge("bridge_speed", {"vehicle": {"speed_kmh_backup": 57}})
        state.mark_stale_sources(stale_after_ms=2500)

        self.assertFalse(state.resolve("nav.connected"))
        self.assertEqual(57, state.resolve("vehicle.speed_kmh_backup"))

    def test_android_inactive_navigation_packet_clears_previous_guidance(self) -> None:
        state = HudState(
            {
                "nav": {
                    "connected": True,
                    "distance_meters": 300,
                    "time_seconds": 25,
                    "road": "Gangnam-daero",
                    "instruction": "Turn right",
                    "turn_side": 2,
                    "event_type": 4,
                }
            }
        )

        source, update = normalize_packet({"type": "navigation", "active": False})
        state.merge(source, update)

        self.assertEqual("bridge_nav", source)
        self.assertFalse(state.resolve("nav.connected"))
        self.assertEqual("--", state.resolve("nav.distance_meters"))
        self.assertEqual("--", state.resolve("nav.time_seconds"))
        self.assertEqual("", state.resolve("nav.road"))
        self.assertEqual("", state.resolve("nav.instruction"))
        self.assertEqual("--", state.resolve("nav.turn_side"))
        self.assertEqual("--", state.resolve("nav.event_type"))

    def test_production_initial_state_clears_layout_dummy_navigation_until_bridge_connects(self) -> None:
        build_initial_state = getattr(state_module, "build_initial_state", None)
        self.assertIsNotNone(build_initial_state)
        layout = {
            "dummy_data": {
                "vehicle": {"source": "dummy", "speed_kmh": 42},
                "nav": {
                    "connected": True,
                    "distance_meters": 300,
                    "time_seconds": 25,
                    "road": "Gangnam-daero",
                    "instruction": "Turn right",
                    "turn_side": 2,
                    "event_type": 4,
                },
            }
        }

        state = build_initial_state(layout, obd_configured=True, can_configured=True, dummy_enabled=False)

        self.assertEqual("pi-local", state.resolve("vehicle.source"))
        self.assertFalse(state.resolve("nav.connected"))
        self.assertEqual("--", state.resolve("nav.distance_meters"))
        self.assertEqual("--", state.resolve("nav.time_seconds"))
        self.assertEqual("", state.resolve("nav.road"))
        self.assertEqual("", state.resolve("nav.instruction"))
        self.assertEqual("--", state.resolve("nav.turn_side"))
        self.assertEqual("--", state.resolve("nav.event_type"))

    def test_production_initial_state_clears_live_vehicle_dummy_values_until_pi_input_arrives(self) -> None:
        build_initial_state = getattr(state_module, "build_initial_state", None)
        self.assertIsNotNone(build_initial_state)
        layout = {
            "dummy_data": {
                "vehicle": {
                    "source": "dummy",
                    "speed_kmh": 42,
                    "speed_kmh_backup": 41,
                    "rpm": 1850,
                    "coolant_c": 88,
                    "voltage_v": 14.1,
                    "fuel_percent": 72,
                    "gear_range": "D",
                    "gear_actual": "3",
                    "atf_c": 84,
                    "pedal_percent": 18,
                }
            }
        }

        state = build_initial_state(layout, obd_configured=True, can_configured=True, dummy_enabled=False)

        self.assertEqual("pi-local", state.resolve("vehicle.source"))
        self.assertIsNone(state.resolve("vehicle.speed_kmh", None))
        self.assertIsNone(state.resolve("vehicle.speed_kmh_backup", None))
        self.assertIsNone(state.resolve("vehicle.rpm", None))
        self.assertIsNone(state.resolve("vehicle.coolant_c", None))
        self.assertIsNone(state.resolve("vehicle.voltage_v", None))
        self.assertIsNone(state.resolve("vehicle.fuel_percent", None))
        self.assertIsNone(state.resolve("vehicle.gear_range", None))
        self.assertIsNone(state.resolve("vehicle.gear_actual", None))
        self.assertIsNone(state.resolve("vehicle.atf_c", None))
        self.assertIsNone(state.resolve("vehicle.pedal_percent", None))

    def test_stale_obd_speed_is_cleared_so_android_backup_speed_can_render(self) -> None:
        state = HudState(
            {
                "vehicle": {
                    "source": "pi-obd",
                    "speed_kmh": 72,
                    "speed_kmh_backup": 57,
                    "rpm": 2100,
                    "coolant_c": 88,
                    "voltage_v": 14.1,
                    "obd_state": "live",
                }
            }
        )
        state.merge("obd", {"vehicle": {"speed_kmh": 72, "rpm": 2100, "coolant_c": 88, "voltage_v": 14.1}})
        state.updated_at["obd"] = time.monotonic() - 3

        state.mark_stale_sources(stale_after_ms=2500)

        self.assertEqual("stale", state.resolve("vehicle.obd_state"))
        self.assertIsNone(state.resolve("vehicle.speed_kmh", None))
        self.assertIsNone(state.resolve("vehicle.rpm", None))
        self.assertIsNone(state.resolve("vehicle.coolant_c", None))
        self.assertIsNone(state.resolve("vehicle.voltage_v", None))
        self.assertEqual(57, state.resolve_first(["vehicle.speed_kmh", "vehicle.speed_kmh_backup"]))

    def test_stale_android_backup_speed_is_cleared_when_bridge_speed_stops(self) -> None:
        state = HudState({"vehicle": {"speed_kmh": None, "speed_kmh_backup": 57}})
        state.merge("bridge_speed", {"vehicle": {"speed_kmh_backup": 57}})
        state.updated_at["bridge_speed"] = time.monotonic() - 3

        state.mark_stale_sources(stale_after_ms=2500)

        self.assertIsNone(state.resolve("vehicle.speed_kmh_backup", None))
        self.assertEqual("--", state.resolve_first(["vehicle.speed_kmh", "vehicle.speed_kmh_backup"]))

    def test_stale_can_source_clears_can_decoded_vehicle_values(self) -> None:
        state = HudState({"vehicle": {"can_state": "live", "gear_actual": "D", "pedal_percent": 40}})
        state.merge("can", {"vehicle": {"can_state": "live", "gear_actual": "D", "pedal_percent": 40}})
        state.updated_at["can"] = time.monotonic() - 3

        state.mark_stale_sources(stale_after_ms=2500)

        self.assertEqual("stale", state.resolve("vehicle.can_state"))
        self.assertIsNone(state.resolve("vehicle.gear_actual", None))
        self.assertIsNone(state.resolve("vehicle.pedal_percent", None))

    def test_remote_vehicle_status_packet_does_not_override_pi_local_vehicle_values(self) -> None:
        source, update = normalize_packet(
            {
                "type": "vehicle_status",
                "speed_kmh_obd": 99,
                "rpm": 4100,
                "coolant_c": 96,
                "source": "android",
            }
        )

        self.assertEqual("vehicle_status", source)
        self.assertEqual({}, update)

    def test_android_diagnostic_packets_are_ignored_by_default(self) -> None:
        for packet in (
            {"type": "dtc_snapshot", "stored": ["P0133"], "pending": [], "permanent": []},
            {"type": "vehicle_debug", "can_frame_count": 128, "last_can_id": "0x316"},
        ):
            source, update = normalize_packet(packet)

            self.assertEqual("ignored", source)
            self.assertEqual({}, update)

    def test_unknown_android_packet_types_are_ignored_instead_of_becoming_navigation(self) -> None:
        for packet in (
            {"type": "unknown_navigation_fields", "distance_meters": 999, "road": "Wrong road"},
            {"type": "unknown_inactive", "active": False},
        ):
            source, update = normalize_packet(packet)

            self.assertEqual("ignored", source)
            self.assertEqual({}, update)

    def test_initial_vehicle_status_labels_dummy_mode_without_claiming_live_obd(self) -> None:
        update = initial_vehicle_status_update(obd_configured=False, can_configured=False, dummy_enabled=True)

        self.assertEqual(
            {
                "vehicle": {
                    "source": "dummy",
                    "obd_state": "not-configured",
                    "can_state": "not-configured",
                }
            },
            update,
        )

    def test_initial_vehicle_status_labels_configured_local_inputs_before_live_data_arrives(self) -> None:
        update = initial_vehicle_status_update(obd_configured=True, can_configured=True, dummy_enabled=False)

        self.assertEqual(
            {
                "vehicle": {
                    "source": "pi-local",
                    "obd_state": "configured",
                    "can_state": "configured",
                }
            },
            update,
        )

    def test_resolve_first_prefers_primary_obd_speed_over_android_backup(self) -> None:
        state = HudState(
            {
                "vehicle": {
                    "speed_kmh": 42,
                    "speed_kmh_backup": 57,
                }
            }
        )

        self.assertEqual(42, state.resolve_first(["vehicle.speed_kmh", "vehicle.speed_kmh_backup"]))

    def test_resolve_first_uses_android_backup_when_primary_missing(self) -> None:
        state = HudState({"vehicle": {"speed_kmh": None, "speed_kmh_backup": 57}})

        self.assertEqual(57, state.resolve_first(["vehicle.speed_kmh", "vehicle.speed_kmh_backup"]))

    def test_merge_ignores_none_values_so_transient_obd_read_failures_do_not_blank_values(self) -> None:
        state = HudState({"vehicle": {"speed_kmh": 42, "rpm": 1850}})

        state.merge("obd", {"vehicle": {"speed_kmh": None, "rpm": 1900}})

        self.assertEqual(42, state.resolve("vehicle.speed_kmh"))
        self.assertEqual(1900, state.resolve("vehicle.rpm"))

    def test_dummy_merge_only_fills_missing_values_when_pi_local_source_is_active(self) -> None:
        state = HudState(
            {
                "vehicle": {
                    "source": "pi-obd",
                    "speed_kmh": 72,
                    "rpm": 2400,
                    "atf_c": None,
                },
                "warnings": {
                    "check_engine": True,
                },
            }
        )

        state.merge(
            "dummy",
            {
                "vehicle": {
                    "source": "dummy",
                    "speed_kmh": 42,
                    "rpm": 1850,
                    "atf_c": 84,
                },
                "warnings": {
                    "check_engine": False,
                    "door_open": False,
                },
            },
        )

        self.assertEqual("pi-obd", state.resolve("vehicle.source"))
        self.assertEqual(72, state.resolve("vehicle.speed_kmh"))
        self.assertEqual(2400, state.resolve("vehicle.rpm"))
        self.assertEqual(84, state.resolve("vehicle.atf_c"))
        self.assertTrue(state.resolve("warnings.check_engine"))
        self.assertFalse(state.resolve("warnings.door_open"))

    def test_dummy_merge_can_update_values_when_dummy_is_the_active_source(self) -> None:
        state = HudState({"vehicle": {"source": "dummy", "speed_kmh": 42}})

        state.merge("dummy", {"vehicle": {"source": "dummy", "speed_kmh": 51}})

        self.assertEqual("dummy", state.resolve("vehicle.source"))
        self.assertEqual(51, state.resolve("vehicle.speed_kmh"))

    def test_vehicle_debug_packet_updates_debug_values_when_diagnostic_udp_is_enabled(self) -> None:
        source, update = normalize_packet(
            {
                "type": "vehicle_debug",
                "can_frame_count": 128,
                "last_can_id": "0x316",
                "obd_request": "010C",
                "obd_response": "7E8 04 41 0C 1A F8",
            },
            allow_diagnostic_packets=True,
        )

        self.assertEqual("debug", source)
        self.assertEqual(
            {
                "debug": {
                    "can_frame_count": 128,
                    "last_can_id": "0x316",
                    "obd_request": "010C",
                    "obd_response": "7E8 04 41 0C 1A F8",
                }
            },
            update,
        )

    def test_dtc_snapshot_packet_updates_dtc_values_when_diagnostic_udp_is_enabled(self) -> None:
        source, update = normalize_packet(
            {
                "type": "dtc_snapshot",
                "stored": ["P0133"],
                "pending": ["P0300"],
                "permanent": [],
            },
            allow_diagnostic_packets=True,
        )

        self.assertEqual("dtc", source)
        self.assertEqual(
            {
                "dtc": {
                    "stored": ["P0133"],
                    "pending": ["P0300"],
                    "permanent": [],
                    "count": 2,
                }
            },
            update,
        )

    def test_discovery_probe_and_hello_match_bridge_contract(self) -> None:
        self.assertTrue(parse_discovery_probe(b'{"type":"headunit_hud_discover"}'))
        self.assertFalse(parse_discovery_probe(b'{"type":"other"}'))

        hello = json.loads(build_discovery_hello("Headunit Pi HUD", "192.168.43.20", 4210).decode("utf-8"))
        self.assertEqual("headunit_hud_hello", hello["type"])
        self.assertEqual("Headunit Pi HUD", hello["name"])
        self.assertEqual("192.168.43.20", hello["ip"])
        self.assertEqual(4210, hello["udp_port"])
        self.assertEqual(DEVICE_KIND_PI_HUD, hello["device_kind"])

    def test_esp32_settings_packet_is_ignored_by_pi_runtime(self) -> None:
        source, update = normalize_packet({"type": "settings", "debug_overlay": True})

        self.assertEqual("settings", source)
        self.assertEqual({}, update)


if __name__ == "__main__":
    unittest.main()
