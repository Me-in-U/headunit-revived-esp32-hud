from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .can_signals import decode_can_signals, merge_nested_update
from .source_threads import SourceThread, StateCallback


@dataclass
class CanFrameSummary:
    frame_count: int = 0
    last_arbitration_id: int | None = None


class SocketCanSource(SourceThread):
    def __init__(self, callback: StateCallback, channel: str = "can0", signal_definitions: list[dict[str, Any]] | None = None) -> None:
        super().__init__(callback, "socketcan")
        self.channel = channel
        self.signal_definitions = signal_definitions or []

    def run(self) -> None:
        try:
            import can
        except ImportError:
            self.callback("can", {"vehicle": {"can_state": "python-can-missing"}})
            return
        summary = CanFrameSummary()
        try:
            try:
                bus = can.interface.Bus(channel=self.channel, interface="socketcan")
            except TypeError:
                bus = can.interface.Bus(channel=self.channel, bustype="socketcan")
            while not self.stop_event.is_set():
                message = bus.recv(timeout=0.5)
                if message is None:
                    continue
                summary.frame_count += 1
                summary.last_arbitration_id = int(message.arbitration_id)
                update = {
                    "vehicle": {
                        "can_state": "live",
                    },
                    "debug": {
                        "can_frame_count": summary.frame_count,
                        "last_can_id": hex(summary.last_arbitration_id),
                    },
                }
                decoded = decode_can_signals(summary.last_arbitration_id, bytes(message.data), self.signal_definitions)
                merge_nested_update(update, decoded)
                self.callback("can", update)
        except Exception as exc:
            self.callback("can", {"vehicle": {"can_state": f"error:{exc.__class__.__name__}"}})
