from __future__ import annotations

import threading
from typing import Any, Callable


StateCallback = Callable[[str, dict[str, Any]], None]


class SourceThread(threading.Thread):
    def __init__(self, callback: StateCallback, name: str) -> None:
        super().__init__(daemon=True, name=name)
        self.callback = callback
        self.stop_event = threading.Event()
        self.ready_event = threading.Event()

    def stop(self) -> None:
        self.stop_event.set()
