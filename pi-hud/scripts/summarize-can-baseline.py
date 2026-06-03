#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PI_DIR = Path(__file__).resolve().parents[1]
if str(PI_DIR) not in sys.path:
    sys.path.insert(0, str(PI_DIR))

from hud_pi.vehicle_baseline import summarize_can_records


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize CAN IDs from a collected Raspberry Pi HUD baseline JSON")
    parser.add_argument("baseline", help="Baseline JSON from collect-vehicle-baseline.py")
    parser.add_argument("--output", default="", help="Write summary JSON here. Defaults to <baseline>-can-summary.json")
    parser.add_argument("--sample-limit", type=int, default=3)
    return parser


def default_output_path(baseline: Path) -> Path:
    return baseline.with_name(f"{baseline.stem}-can-summary.json")


def build_summary(report: dict[str, Any], sample_limit: int = 3) -> dict[str, Any]:
    can = report.get("can", {})
    records = can.get("records", []) if isinstance(can, dict) else []
    if not isinstance(records, list):
        records = []
    return {
        "schema_version": 1,
        "vehicle": report.get("vehicle", "unknown"),
        "source_baseline_created_at": report.get("created_at", ""),
        "can": {
            "configured": bool(can.get("configured")) if isinstance(can, dict) else False,
            "channel": can.get("channel", "") if isinstance(can, dict) else "",
            "duration_seconds": can.get("duration_seconds") if isinstance(can, dict) else None,
        },
        "can_summary": summarize_can_records(records, sample_limit=sample_limit),
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    baseline_path = Path(args.baseline)
    with baseline_path.open("r", encoding="utf-8") as handle:
        report = json.load(handle)
    summary = build_summary(report, sample_limit=args.sample_limit)
    output = Path(args.output) if args.output else default_output_path(baseline_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] CAN summary written: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
