#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
PI_HUD_DIR = ROOT_DIR / "pi-hud"
if str(PI_HUD_DIR) not in sys.path:
    sys.path.insert(0, str(PI_HUD_DIR))

from hud_pi.field_pack import (  # noqa: E402
    DEFAULT_ENV_EXAMPLE,
    DEFAULT_LAYOUT,
    DEFAULT_NAV_ASSETS_DIR,
    DEFAULT_OUTPUT,
    DEFAULT_VEHICLES_DIR,
    DEFAULT_WARNING_ASSETS_DIR,
    build_field_pack_from_file,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a Raspberry Pi HUD field-transfer package")
    parser.add_argument("--layout", default=DEFAULT_LAYOUT, help="Layout JSON to place under layouts/ in the zip")
    parser.add_argument("--vehicles-dir", default=DEFAULT_VEHICLES_DIR, help="Directory of vehicle profile JSON files")
    parser.add_argument("--env-example", default=DEFAULT_ENV_EXAMPLE, help="Environment example copied as config/pi-hud.env.example")
    parser.add_argument("--assets-dir", default=DEFAULT_WARNING_ASSETS_DIR, help="Warning icon assets copied into pi-hud/assets/")
    parser.add_argument("--nav-assets-dir", default=DEFAULT_NAV_ASSETS_DIR, help="Navigation icon assets copied into pi-hud/assets/")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output zip path")
    parser.add_argument("--width", type=int, default=1920, help="Expected HUD render width")
    parser.add_argument("--height", type=int, default=480, help="Expected HUD render height")
    handoff = parser.add_mutually_exclusive_group()
    handoff.add_argument("--require-handoff", dest="require_handoff", action="store_true", default=True)
    handoff.add_argument("--no-require-handoff", dest="require_handoff", action="store_false")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        package = build_field_pack(args)
    except ValueError as error:
        print(f"[FAIL] {error}", file=sys.stderr)
        return 1

    print(f"[OK] wrote {package}")
    return 0


def build_field_pack(args: argparse.Namespace) -> Path:
    result = build_field_pack_from_file(
        layout_path=resolve_path(args.layout),
        vehicles_dir=resolve_path(args.vehicles_dir),
        env_example_path=resolve_path(args.env_example),
        warning_assets_dir=resolve_path(args.assets_dir),
        nav_assets_dir=resolve_path(args.nav_assets_dir),
        output_path=resolve_path(args.output),
        width=args.width,
        height=args.height,
        require_handoff=args.require_handoff,
        repo_root=ROOT_DIR,
    )
    return result.output


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT_DIR / path


if __name__ == "__main__":
    raise SystemExit(main())
