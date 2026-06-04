#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

PI_DIR = Path(__file__).resolve().parents[1]
if str(PI_DIR) not in sys.path:
    sys.path.insert(0, str(PI_DIR))

from hud_pi.ble_obd_discovery import characteristic_infos_from_services, classify_ble_obd_characteristics, env_lines_for_ble_obd


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect BLE ELM327/iCar characteristics and print Pi HUD env values")
    parser.add_argument("mac", help="BLE MAC/address of the iCar/ELM327 adapter")
    return parser


async def inspect_ble_obd(mac: str) -> int:
    try:
        from bleak import BleakClient
    except ImportError:
        print("[FAIL] bleak is not installed. Install pi-hud requirements first.", file=sys.stderr)
        return 2

    async with BleakClient(mac) as client:
        services = getattr(client, "services", None)
        if services is None:
            services = await client.get_services()
        characteristics = characteristic_infos_from_services(services)
    result = classify_ble_obd_characteristics(characteristics)

    print(f"[OK] inspected {len(characteristics)} BLE characteristics for {mac}")
    print("Notify/indicate candidates (adapter -> Pi):")
    for item in result.rx_candidates:
        print(f"  {item.uuid}  service={item.service_uuid}  properties={','.join(item.properties)}")
    print("Write candidates (Pi -> adapter):")
    for item in result.tx_candidates:
        print(f"  {item.uuid}  service={item.service_uuid}  properties={','.join(item.properties)}")

    if not result.pairs:
        print("[FAIL] no notify/write characteristic pair found", file=sys.stderr)
        return 1

    first = result.pairs[0]
    print("Suggested /etc/headunit-pi-hud.env lines:")
    for line in env_lines_for_ble_obd(mac, first.rx_uuid, first.tx_uuid):
        print(line)
    print("After saving these values, run: python pi-hud/scripts/diagnose-inputs.py")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return asyncio.run(inspect_ble_obd(args.mac))


if __name__ == "__main__":
    raise SystemExit(main())
