from __future__ import annotations

import os
import signal
from collections.abc import Callable, Iterable
from typing import Any

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from .renderer import HudRenderer
from .state import HudState


def make_state_merger(state: HudState, lock: Any) -> Callable[[str, dict], None]:
    def merge(source: str, update: dict) -> None:
        with lock:
            state.merge(source, update)

    return merge


def run_sources(sources: Iterable[Any], loop: Callable[[], int]) -> int:
    source_list = list(sources)
    for source in source_list:
        source.start()
    try:
        return loop()
    finally:
        for source in source_list:
            source.stop()


def run_pygame_loop(
    args: Any,
    layout: dict[str, Any],
    state: HudState,
    lock: Any,
    *,
    pygame_module: Any = pygame,
    renderer_factory: Callable[[dict[str, Any], Any], HudRenderer] = HudRenderer,
    signal_module: Any = signal,
) -> int:
    pygame_module.init()
    flags = 0 if args.windowed else pygame_module.FULLSCREEN
    screen = pygame_module.display.set_mode((args.width, args.height), flags)
    pygame_module.display.set_caption("Headunit Pi HUD")
    renderer = renderer_factory(layout, screen)
    clock = pygame_module.time.Clock()
    running = True

    def stop(_signum: int, _frame: object) -> None:
        nonlocal running
        running = False

    previous_sigint = signal_module.signal(signal_module.SIGINT, stop)
    previous_sigterm = signal_module.signal(signal_module.SIGTERM, stop)
    try:
        while running:
            for event in pygame_module.event.get():
                if event.type == pygame_module.QUIT:
                    running = False
                elif event.type == pygame_module.KEYDOWN and event.key in (pygame_module.K_ESCAPE, pygame_module.K_q):
                    running = False
            with lock:
                state.mark_stale_sources()
                renderer.render(state)
            pygame_module.display.flip()
            clock.tick(30)
    finally:
        signal_module.signal(signal_module.SIGINT, previous_sigint)
        signal_module.signal(signal_module.SIGTERM, previous_sigterm)
        pygame_module.quit()
    return 0
