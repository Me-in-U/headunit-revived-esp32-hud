from __future__ import annotations

import unittest
from types import SimpleNamespace

from hud_pi.runtime_loop import make_state_merger, run_pygame_loop, run_sources


class RuntimeLoopTest(unittest.TestCase):
    def test_make_state_merger_updates_state_under_lock(self) -> None:
        calls: list[tuple[str, object, object | None]] = []
        state = FakeState(calls)
        lock = FakeLock(calls)

        merge = make_state_merger(state, lock)
        merge("can", {"vehicle": {"speed_kmh": 88}})

        self.assertEqual(
            [
                ("lock-enter", lock, None),
                ("merge", "can", {"vehicle": {"speed_kmh": 88}}),
                ("lock-exit", lock, None),
            ],
            calls,
        )

    def test_run_sources_stops_sources_even_when_loop_raises(self) -> None:
        calls: list[str] = []
        sources = [FakeSource("bridge", calls), FakeSource("dummy", calls)]

        with self.assertRaises(RuntimeError):
            run_sources(sources, lambda: raise_runtime_error("loop failed"))

        self.assertEqual(["start:bridge", "start:dummy", "stop:bridge", "stop:dummy"], calls)

    def test_run_pygame_loop_renders_quit_frame_and_restores_signals(self) -> None:
        calls: list[object] = []
        pygame = FakePygame(calls)
        signal_module = FakeSignal(calls)
        args = SimpleNamespace(width=1920, height=480, windowed=True)
        layout = {"canvas": {"width": 1920, "height": 480}}
        state = FakeState(calls)
        lock = FakeLock(calls)

        exit_code = run_pygame_loop(
            args,
            layout,
            state,
            lock,
            pygame_module=pygame,
            renderer_factory=lambda actual_layout, screen: FakeRenderer(calls, actual_layout, screen),
            signal_module=signal_module,
        )

        self.assertEqual(0, exit_code)
        self.assertEqual(
            [
                "pygame-init",
                ("set-mode", (1920, 480), 0),
                ("caption", "Headunit Pi HUD"),
                "clock",
                ("signal", signal_module.SIGINT),
                ("signal", signal_module.SIGTERM),
                "events",
                ("lock-enter", lock, None),
                "stale",
                ("render", layout, "screen"),
                ("lock-exit", lock, None),
                "flip",
                ("tick", 30),
                ("signal", signal_module.SIGINT),
                ("signal", signal_module.SIGTERM),
                "pygame-quit",
            ],
            calls,
        )


class FakeLock:
    def __init__(self, calls: list[object]) -> None:
        self.calls = calls

    def __enter__(self) -> None:
        self.calls.append(("lock-enter", self, None))

    def __exit__(self, *_exc: object) -> None:
        self.calls.append(("lock-exit", self, None))


class FakeState:
    def __init__(self, calls: list[object]) -> None:
        self.calls = calls

    def merge(self, source: str, update: dict) -> None:
        self.calls.append(("merge", source, update))

    def mark_stale_sources(self) -> None:
        self.calls.append("stale")


class FakeSource:
    def __init__(self, name: str, calls: list[str]) -> None:
        self.name = name
        self.calls = calls

    def start(self) -> None:
        self.calls.append(f"start:{self.name}")

    def stop(self) -> None:
        self.calls.append(f"stop:{self.name}")


class FakeRenderer:
    def __init__(self, calls: list[object], layout: dict, screen: object) -> None:
        self.calls = calls
        self.layout = layout
        self.screen = screen

    def render(self, _state: FakeState) -> None:
        self.calls.append(("render", self.layout, self.screen))


class FakePygame:
    FULLSCREEN = 1
    KEYDOWN = 2
    K_ESCAPE = 27
    K_q = 113
    QUIT = 3

    def __init__(self, calls: list[object]) -> None:
        self.calls = calls
        self.display = FakeDisplay(calls)
        self.event = FakeEvents(self)
        self.time = FakeTime(calls)

    def init(self) -> None:
        self.calls.append("pygame-init")

    def quit(self) -> None:
        self.calls.append("pygame-quit")


class FakeDisplay:
    def __init__(self, calls: list[object]) -> None:
        self.calls = calls

    def set_mode(self, size: tuple[int, int], flags: int) -> str:
        self.calls.append(("set-mode", size, flags))
        return "screen"

    def set_caption(self, caption: str) -> None:
        self.calls.append(("caption", caption))

    def flip(self) -> None:
        self.calls.append("flip")


class FakeEvents:
    def __init__(self, pygame: FakePygame) -> None:
        self.pygame = pygame

    def get(self) -> list[SimpleNamespace]:
        self.pygame.calls.append("events")
        return [SimpleNamespace(type=self.pygame.QUIT)]


class FakeTime:
    def __init__(self, calls: list[object]) -> None:
        self.calls = calls

    def Clock(self) -> "FakeClock":
        self.calls.append("clock")
        return FakeClock(self.calls)


class FakeClock:
    def __init__(self, calls: list[object]) -> None:
        self.calls = calls

    def tick(self, fps: int) -> None:
        self.calls.append(("tick", fps))


class FakeSignal:
    SIGINT = 2
    SIGTERM = 15

    def __init__(self, calls: list[object]) -> None:
        self.calls = calls
        self.previous: dict[int, object] = {}

    def signal(self, signum: int, handler: object) -> object:
        self.calls.append(("signal", signum))
        previous = self.previous.get(signum, f"old:{signum}")
        self.previous[signum] = handler
        return previous


def raise_runtime_error(message: str) -> None:
    raise RuntimeError(message)


if __name__ == "__main__":
    unittest.main()
