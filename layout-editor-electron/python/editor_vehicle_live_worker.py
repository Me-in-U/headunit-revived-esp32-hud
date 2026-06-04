from __future__ import annotations

import json
import sys

from editor_vehicle_live import run_worker


def main() -> int:
    raw = sys.stdin.buffer.read().decode("utf-8").strip()
    config = json.loads(raw) if raw else {}
    if not isinstance(config, dict):
        raise ValueError("worker config must be a JSON object")
    run_worker(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
