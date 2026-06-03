#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PI_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = PI_DIR.parent
if str(PI_DIR) not in sys.path:
    sys.path.insert(0, str(PI_DIR))

from hud_pi.diagnostics import load_env_file
from hud_pi.first_run import build_first_run_report, default_report_path


def default_env_file_path() -> Path:
    configured = os.environ.get("HEADUNIT_HUD_ENV_FILE", "").strip()
    if configured:
        return Path(configured)
    return Path("/etc/headunit-pi-hud.env")


def load_runtime_environment() -> list[str]:
    return load_env_file(default_env_file_path(), os.environ)


def default_layout_path() -> str:
    return os.environ.get(
        "HEADUNIT_HUD_LAYOUT",
        str(ROOT_DIR / "layouts" / "avante_hd_2010_default.json"),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize first-run readiness for the Raspberry Pi HUD")
    parser.add_argument("--layout", default=default_layout_path())
    parser.add_argument("--output", default=os.environ.get("HEADUNIT_HUD_FIRST_RUN_OUTPUT", str(default_report_path(os.environ.get("HEADUNIT_HUD_APP_DIR", ROOT_DIR)))))
    parser.add_argument("--json", action="store_true", help="Print the full JSON report")
    parser.add_argument("--no-write", action="store_true", help="Do not write the JSON report to --output")
    parser.add_argument("--probe-inputs", action="store_true", help="Run live OBD/CAN probes and include their result")
    parser.add_argument("--probe-display", action="store_true", help="Read the Pi framebuffer size and verify 1920x480 output")
    parser.add_argument("--obd-timeout", type=float, default=2.0)
    parser.add_argument("--can-timeout", type=float, default=3.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    load_runtime_environment()
    args = build_parser().parse_args(argv)
    os.environ["HEADUNIT_HUD_LAYOUT"] = args.layout
    report = build_first_run_report(
        os.environ,
        probe_inputs=args.probe_inputs,
        obd_timeout=args.obd_timeout,
        can_timeout=args.can_timeout,
        probe_display_output=args.probe_display,
    )

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_report(report))

    if not args.no_write:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return 0 if report["standalone_ready"] and (not args.probe_inputs or report["live_input_ready"]) and (not args.probe_display or report["display_ready"]) else 1


def format_report(report: dict) -> str:
    lines = [
        f"Pi standalone ready: {'yes' if report['standalone_ready'] else 'no'}",
        f"Layout: {'OK' if report['layout']['ok'] else 'FAIL'} - {report['layout']['detail']}",
        f"Display: {report['display']['width']}x{report['display']['height']}",
        f"OBD: {report['obd']['transport']}",
        f"CAN: {report['can']['channel'] or 'not-configured'}",
        f"Android bridge: {report['android_bridge']['role']} (optional)",
    ]
    if report["input_probes"]["enabled"]:
        lines.extend(
            [
                f"OBD probe: {'OK' if report['input_probes']['obd']['ok'] else 'FAIL'} - {report['input_probes']['obd']['detail']}",
                f"CAN probe: {'OK' if report['input_probes']['can']['ok'] else 'FAIL'} - {report['input_probes']['can']['detail']}",
            ]
        )
    if report["display"]["probe"]["enabled"]:
        lines.append(f"Display probe: {'OK' if report['display']['probe']['ok'] else 'FAIL'} - {report['display']['probe']['detail']}")
    if report["blocking_issues"]:
        lines.append("Blocking issues:")
        lines.extend(f"- {issue}" for issue in report["blocking_issues"])
    if report["probe_issues"]:
        lines.append("Probe issues:")
        lines.extend(f"- {issue}" for issue in report["probe_issues"])
    if report["next_steps"]:
        lines.append("Next steps:")
        lines.extend(f"- {step}" for step in report["next_steps"])
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
