#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


PI_DIR = Path(__file__).resolve().parents[1]
if str(PI_DIR) not in sys.path:
    sys.path.insert(0, str(PI_DIR))

from hud_pi.field_pack import apply_field_pack_package


DEFAULT_APP_DIR = "/opt/headunit-pi-hud"
DEFAULT_ENV_FILE = "/etc/headunit-pi-hud.env"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify and apply a Raspberry Pi HUD field-transfer package")
    parser.add_argument("package", help="headunit-pi-field-pack.zip")
    parser.add_argument("--app-dir", default=DEFAULT_APP_DIR, help="Installed Pi HUD app directory")
    parser.add_argument("--env-file", default=DEFAULT_ENV_FILE, help="Runtime environment file")
    parser.add_argument("--overwrite-env", action="store_true", help="Replace env-file with config/pi-hud.env.example")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = apply_field_pack(args)
    except ValueError as error:
        print(f"[FAIL] {error}", file=sys.stderr)
        return 1

    print(f"[OK] applied {report['layout']} to {report['app_dir']}")
    if report["env_written"]:
        print(f"[OK] wrote env file {report['env_file']}")
    else:
        print(f"[SKIP] preserved existing env file {report['env_file']}")
    return 0


def apply_field_pack(args: argparse.Namespace) -> dict[str, Any]:
    result = apply_field_pack_package(
        package_path=Path(args.package),
        app_dir=Path(args.app_dir),
        env_file=Path(args.env_file),
        overwrite_env=args.overwrite_env,
    )

    return {
        "app_dir": str(result.app_dir),
        "env_file": str(result.env_file),
        "env_written": result.env_written,
        "layout": str(result.layout),
        "vehicles": [str(path) for path in result.vehicles],
    }


if __name__ == "__main__":
    raise SystemExit(main())
