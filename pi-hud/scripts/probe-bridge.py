#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PI_DIR = Path(__file__).resolve().parents[1]
if str(PI_DIR) not in sys.path:
    sys.path.insert(0, str(PI_DIR))

from hud_pi.bridge_probe import discover_pi_hud, send_sample_bridge_packets


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Probe a Raspberry Pi HUD discovery target and send sample Android bridge packets")
    parser.add_argument("host", nargs="?", default="255.255.255.255", help="Pi host or broadcast address")
    parser.add_argument("--discovery-port", type=int, default=4211)
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--send-sample", action="store_true", help="Send one sample navigation packet and one backup speed packet")
    parser.add_argument("--speed", type=int, default=42)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        hello = discover_pi_hud(args.host, discovery_port=args.discovery_port, timeout=args.timeout)
    except OSError as exc:
        print(f"[FAIL] discovery socket error: {exc}", file=sys.stderr)
        return 1
    except TimeoutError:
        print("[FAIL] discovery timed out", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"[FAIL] discovery failed: {exc}", file=sys.stderr)
        return 1

    print(f"[OK] discovered {hello.name} at {hello.host}:{hello.udp_port} ({hello.device_kind})")
    if args.send_sample:
        count = send_sample_bridge_packets(hello.host, hello.udp_port, speed_kmh=args.speed)
        print(f"[OK] sent {count} sample bridge packets to {hello.host}:{hello.udp_port}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
