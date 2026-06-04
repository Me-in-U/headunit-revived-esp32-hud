#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PI_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = PI_DIR.parent
if str(PI_DIR) not in sys.path:
    sys.path.insert(0, str(PI_DIR))

from hud_pi.layout_verifier import verify_layout_file


def default_layout_path() -> str:
    return os.environ.get(
        "HEADUNIT_HUD_LAYOUT",
        str(ROOT_DIR / "layouts" / "avante_hd_2010_default.json"),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate and render-check a 1920x480 Pi HUD layout JSON")
    parser.add_argument("layout", nargs="?", default=default_layout_path(), help="Layout JSON path")
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--output", default="", help="Optional PNG snapshot path")
    parser.add_argument("--require-handoff", action="store_true", help="Require editor-generated Pi handoff metadata and digest")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = verify_layout_file(
        args.layout,
        width=args.width,
        height=args.height,
        output=args.output or None,
        require_handoff=args.require_handoff,
    )
    if result.ok:
        print(
            f"[OK] layout: {result.render_size[0]}x{result.render_size[1]}, "
            f"non_background_pixels={result.non_background_pixels}"
        )
        if result.output:
            print(f"[OK] snapshot: {result.output}")
        return 0
    for error in result.errors:
        print(f"[FAIL] {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
