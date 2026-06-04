#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path
import subprocess
import sys


PI_DIR = Path(__file__).resolve().parents[1]
if str(PI_DIR) not in sys.path:
    sys.path.insert(0, str(PI_DIR))

from hud_pi.ble_obd_discovery import characteristic_infos_from_services, classify_ble_obd_characteristics
from hud_pi.diagnostics import load_env_file, probe_can, probe_obd, probe_obd_ble
from hud_pi.hardware_autoconfig import (
    BleObdPair,
    auto_configure_hardware,
    merge_env_updates,
    parse_bluetoothctl_devices,
    parse_can_channels,
)


DEFAULT_ENV_FILE = "/etc/headunit-pi-hud.env"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Auto-detect Raspberry Pi HUD iCar/ELM327 and CANable settings")
    parser.add_argument("--env-file", default=DEFAULT_ENV_FILE, help="Runtime env file to read and optionally update")
    parser.add_argument("--apply", action="store_true", help="Write detected values to the env file")
    parser.add_argument("--force", action="store_true", help="Replace existing OBD/CAN env values when a device is detected")
    parser.add_argument("--scan-seconds", type=float, default=6.0, help="Bluetooth active scan duration before reading known devices")
    parser.add_argument("--no-active-scan", action="store_true", help="Skip bluetoothctl scan and use already-known devices only")
    parser.add_argument("--no-restart", action="store_true", help="Do not restart headunit-pi-hud.service after applying changes")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    env_file = Path(args.env_file)
    environ = dict(os.environ)
    load_env_file(env_file, environ, override=True)

    if not args.no_active_scan:
        run_bluetooth_scan(args.scan_seconds)

    result = auto_configure_hardware(
        environ,
        bluetooth_devices=list_bluetooth_devices(),
        can_channels=list_can_channels(),
        rfcomm_bind=bind_rfcomm,
        probe_serial_obd=lambda port, baud: probe_obd(port, baud),
        discover_ble_obd=discover_ble_pairs,
        probe_ble_obd=lambda mac, rx_uuid, tx_uuid: probe_obd_ble(mac, rx_uuid, tx_uuid),
        setup_can=setup_can_channel,
        probe_can_channel=lambda channel: probe_can(channel),
        force=args.force,
    )

    for note in result.notes:
        print(f"[OK] {note}")
    for issue in result.issues:
        print(f"[WARN] {issue}", file=sys.stderr)

    if result.updates:
        print("[OK] detected env updates:")
        for key, value in result.updates.items():
            print(f"{key}={value}")
    else:
        print("[OK] no env updates needed")

    if args.apply and result.updates:
        current = env_file.read_text(encoding="utf-8") if env_file.exists() else ""
        env_file.write_text(merge_env_updates(current, result.updates), encoding="utf-8")
        print(f"[OK] wrote {env_file}")
        if not args.no_restart:
            restart_service()

    return 0


def run_bluetooth_scan(seconds: float) -> None:
    if seconds <= 0:
        return
    command = ["timeout", f"{seconds:g}s", "bluetoothctl", "scan", "on"]
    try:
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=seconds + 2, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return


def list_bluetooth_devices() -> list:
    try:
        completed = subprocess.run(["bluetoothctl", "devices"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return []
    return parse_bluetoothctl_devices(completed.stdout)


def list_can_channels() -> list[str]:
    try:
        completed = subprocess.run(["ip", "-o", "link", "show"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return []
    return parse_can_channels(completed.stdout)


def bind_rfcomm(mac: str, index: int, channel: int) -> str:
    script = PI_DIR / "scripts" / "icar-rfcomm-bind.sh"
    completed = subprocess.run([str(script), mac, str(index), str(channel)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15, check=False)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "rfcomm bind failed")
    return completed.stdout.strip()


def setup_can_channel(channel: str, bitrate: int, listen_only: str) -> None:
    script = PI_DIR / "scripts" / "canable-up.sh"
    completed = subprocess.run([str(script), channel, str(bitrate), listen_only], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15, check=False)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "CAN setup failed")


def discover_ble_pairs(mac: str) -> list[BleObdPair]:
    return asyncio.run(_discover_ble_pairs(mac))


async def _discover_ble_pairs(mac: str) -> list[BleObdPair]:
    from bleak import BleakClient

    async with BleakClient(mac, timeout=6.0) as client:
        services = getattr(client, "services", None)
        if services is None:
            services = await client.get_services()
        characteristics = characteristic_infos_from_services(services)
    result = classify_ble_obd_characteristics(characteristics)
    return [BleObdPair(pair.rx_uuid, pair.tx_uuid) for pair in result.pairs]


def restart_service() -> None:
    subprocess.run(["systemctl", "restart", "headunit-pi-hud.service"], check=False)


if __name__ == "__main__":
    raise SystemExit(main())
