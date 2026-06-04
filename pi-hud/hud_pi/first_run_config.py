from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping


def env_truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def env_int(environ: Mapping[str, str], key: str, fallback: int) -> int:
    try:
        return int(str(environ.get(key, fallback)).strip())
    except (TypeError, ValueError):
        return fallback


def obd_status(environ: Mapping[str, str]) -> dict[str, Any]:
    port = environ.get("HEADUNIT_HUD_OBD_PORT", "").strip()
    baud = env_int(environ, "HEADUNIT_HUD_OBD_BAUD", 38400)
    ble_mac = environ.get("HEADUNIT_HUD_OBD_BLE_MAC", "").strip()
    ble_rx_uuid = environ.get("HEADUNIT_HUD_OBD_BLE_RX_UUID", "").strip()
    ble_tx_uuid = environ.get("HEADUNIT_HUD_OBD_BLE_TX_UUID", "").strip()

    if port:
        return {
            "configured": True,
            "transport": "serial",
            "port": port,
            "baud": baud,
            "issue": "",
        }
    if ble_mac:
        configured = bool(ble_rx_uuid and ble_tx_uuid)
        return {
            "configured": configured,
            "transport": "ble",
            "mac": ble_mac,
            "rx_uuid": ble_rx_uuid,
            "tx_uuid": ble_tx_uuid,
            "issue": "" if configured else "OBD BLE RX/TX UUID is missing",
        }
    return {
        "configured": False,
        "transport": "not-configured",
        "issue": "OBD/iCar input is not configured",
    }


def can_status(environ: Mapping[str, str]) -> dict[str, Any]:
    channel = environ.get("HEADUNIT_HUD_CAN_CHANNEL", "").strip()
    bitrate = env_int(environ, "HEADUNIT_HUD_CAN_BITRATE", 500000)
    listen_only = environ.get("HEADUNIT_HUD_CAN_LISTEN_ONLY", "on").strip() or "on"
    return {
        "configured": bool(channel),
        "channel": channel,
        "bitrate": bitrate,
        "listen_only": listen_only,
        "issue": "" if channel else "CANable SocketCAN channel is not configured",
    }


def bridge_status(environ: Mapping[str, str]) -> dict[str, Any]:
    return {
        "role": "navigation_and_backup_speed_only",
        "required_for_standalone": False,
        "udp_port": env_int(environ, "HEADUNIT_HUD_UDP_PORT", 4210),
        "discovery_port": env_int(environ, "HEADUNIT_HUD_DISCOVERY_PORT", 4211),
        "discovery_enabled": not env_truthy(environ.get("HEADUNIT_HUD_DISABLE_DISCOVERY", "0")),
    }


def next_steps(
    obd: dict[str, Any],
    can: dict[str, Any],
    dummy_enabled: bool,
    probe_inputs: bool = False,
    input_probe_issues: list[str] | None = None,
    probe_display_output: bool = False,
    display_probe_issues: list[str] | None = None,
) -> list[str]:
    steps: list[str] = []
    if dummy_enabled:
        steps.append("Set HEADUNIT_HUD_DUMMY=0 for real Pi standalone use.")
    if not obd["configured"]:
        if obd["transport"] == "ble":
            steps.append("Fill HEADUNIT_HUD_OBD_BLE_RX_UUID and HEADUNIT_HUD_OBD_BLE_TX_UUID, then run diagnose-inputs.py.")
        else:
            steps.append("Set HEADUNIT_HUD_OBD_PORT=/dev/rfcomm0 or configure HEADUNIT_HUD_OBD_BLE_* for iCar Pro 2S.")
    if not can["configured"]:
        steps.append("Set HEADUNIT_HUD_CAN_CHANNEL=can0 and bring CANable up in listen-only mode.")
    if probe_inputs and input_probe_issues:
        steps.append("Fix live OBD/CAN probe failures before relying on real vehicle data.")
    if probe_display_output and display_probe_issues:
        steps.append("Fix the Pi framebuffer/display mode before relying on the 1920x480 HUD.")
    if not steps:
        steps.append("Use the Windows editor Connection/CAN Analysis/OBD Analysis tabs for live simulation, then run diagnose-inputs.py on the Pi.")
    return steps


def default_report_path(app_dir: str | Path = "/opt/headunit-pi-hud") -> Path:
    return Path(app_dir) / "vehicle-baseline" / "first-run-status.json"
