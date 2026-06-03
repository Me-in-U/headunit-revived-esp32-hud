from __future__ import annotations

from typing import Any


def inactive_navigation_update() -> dict[str, Any]:
    return {
        "nav": {
            "connected": False,
            "distance_meters": "--",
            "time_seconds": "--",
            "road": "",
            "instruction": "",
            "turn_side": "--",
            "event_type": "--",
        }
    }


def normalize_packet(packet: dict[str, Any], allow_diagnostic_packets: bool = False) -> tuple[str, dict[str, Any]]:
    packet_type = packet.get("type", "navigation")
    if packet_type == "settings":
        return "settings", {}
    if packet_type == "speed":
        return "bridge_speed", {"vehicle": {"speed_kmh_backup": packet.get("speed_kmh")}}
    if packet_type == "vehicle_status":
        return "vehicle_status", {}
    if packet_type == "dtc_snapshot":
        if not allow_diagnostic_packets:
            return "ignored", {}
        return "dtc", {
            "dtc": {
                "stored": packet.get("stored", []),
                "pending": packet.get("pending", []),
                "permanent": packet.get("permanent", []),
                "count": len(packet.get("stored", [])) + len(packet.get("pending", [])),
            }
        }
    if packet_type == "vehicle_debug":
        if not allow_diagnostic_packets:
            return "ignored", {}
        return "debug", {
            "debug": {
                "can_frame_count": packet.get("can_frame_count"),
                "last_can_id": packet.get("last_can_id"),
                "obd_request": packet.get("obd_request"),
                "obd_response": packet.get("obd_response"),
            }
        }
    if packet_type != "navigation":
        return "ignored", {}
    if packet.get("active") is False:
        return "bridge_nav", inactive_navigation_update()
    return "bridge_nav", {
        "nav": {
            "connected": packet.get("active", True),
            "distance_meters": packet.get("distance_meters"),
            "time_seconds": packet.get("time_seconds"),
            "road": packet.get("road"),
            "instruction": packet.get("instruction") or packet.get("action_text"),
            "turn_side": packet.get("turn_side"),
            "event_type": packet.get("event_type", packet.get("next_event_type")),
        }
    }
