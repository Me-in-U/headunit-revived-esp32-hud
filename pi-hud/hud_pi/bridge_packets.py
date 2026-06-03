from __future__ import annotations

from typing import Any


class SequencedPacketGate:
    def __init__(self) -> None:
        self.last_sequence: int | None = None

    def accepts(self, packet: Any) -> bool:
        if not isinstance(packet, dict):
            return False
        raw_sequence = packet.get("seq")
        if raw_sequence is None:
            return True
        try:
            sequence = int(raw_sequence)
        except (TypeError, ValueError):
            return True
        if self.last_sequence is not None and sequence <= self.last_sequence:
            return False
        self.last_sequence = sequence
        return True
