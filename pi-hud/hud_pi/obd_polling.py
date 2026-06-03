from __future__ import annotations

import re
from typing import Any

from .obd import payload_bytes_after


class Elm327PollingMixin:
    last_obd_request: str
    last_obd_response: str

    def _base_live_vehicle_update(self) -> dict[str, Any]:
        return {"vehicle": {"source": "pi-obd", "obd_state": "live"}}

    def _hex_bytes(self, response: str, service_pid: str) -> list[int]:
        return payload_bytes_after(response, service_pid)

    def _parse_byte_pid_response(self, response: str, service_pid: str, offset: int = 0) -> int | None:
        bytes_ = self._hex_bytes(response, service_pid)
        if not bytes_:
            return None
        return bytes_[0] + offset

    def _parse_rpm_response(self, response: str) -> int | None:
        bytes_ = self._hex_bytes(response, "410C")
        if len(bytes_) < 2:
            return None
        return int(((bytes_[0] * 256) + bytes_[1]) / 4)

    def _parse_voltage_response(self, response: str) -> float | None:
        bytes_ = self._hex_bytes(response, "4142")
        if len(bytes_) >= 2:
            return round(((bytes_[0] * 256) + bytes_[1]) / 1000, 1)
        return None

    def _parse_adapter_voltage(self, response: str) -> float | None:
        match = re.search(r"([-+]?\d+(?:\.\d+)?)\s*V\b", response.upper())
        if match is None:
            return None
        try:
            return round(float(match.group(1)), 1)
        except ValueError:
            return None

    def _parse_mil_response(self, response: str) -> tuple[bool | None, int | None]:
        bytes_ = self._hex_bytes(response, "4101")
        if not bytes_:
            return None, None
        return bool(bytes_[0] & 0x80), bytes_[0] & 0x7F
