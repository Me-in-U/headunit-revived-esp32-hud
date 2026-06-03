from __future__ import annotations

import sys
import threading

from .renderer import HudRenderer, normalize_language
from .runtime_config import (
    build_parser,
    can_configured,
    dummy_enabled,
    load_runtime_layout,
    obd_configured,
)
from .runtime_loop import make_state_merger, run_pygame_loop, run_sources
from .runtime_sources import build_vehicle_sources
from .state import build_initial_state


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        layout = load_runtime_layout(args)
    except ValueError as exc:
        print(f"Layout validation failed: {exc}", file=sys.stderr)
        return 2
    if args.language:
        layout["language"] = normalize_language(args.language, fallback=str(layout.get("language", "en")))
    use_dummy = dummy_enabled(args)
    state = build_initial_state(
        layout,
        obd_configured=obd_configured(args),
        can_configured=can_configured(args),
        dummy_enabled=use_dummy,
    )
    lock = threading.Lock()
    sources = build_vehicle_sources(args, make_state_merger(state, lock), layout=layout)
    return run_sources(sources, lambda: run_pygame_loop(args, layout, state, lock, renderer_factory=HudRenderer))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
