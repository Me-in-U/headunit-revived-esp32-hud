from __future__ import annotations

import time
from typing import Any

from .obd import parse_dtc_response
from .obd_polling import Elm327PollingMixin
from .source_threads import SourceThread, StateCallback


class Elm327ObdSource(SourceThread, Elm327PollingMixin):
    def __init__(self, callback: StateCallback, port: str, baudrate: int = 38400) -> None:
        super().__init__(callback, "elm327-obd")
        self.port = port
        self.baudrate = baudrate
        self.last_obd_request = ""
        self.last_obd_response = ""

    def run(self) -> None:
        try:
            import serial
        except ImportError:
            self.callback("obd", {"vehicle": {"obd_state": "pyserial-missing"}})
            return
        try:
            with serial.Serial(self.port, self.baudrate, timeout=1) as link:
                for command in ("ATZ", "ATE0", "ATL0", "ATS0", "ATH1", "ATSP0"):
                    self._send(link, command)
                    time.sleep(0.15)
                last_dtc_at = 0.0
                while not self.stop_event.is_set():
                    update = self._base_live_vehicle_update()
                    update["vehicle"]["rpm"] = self._read_rpm(link)
                    update["vehicle"]["speed_kmh"] = self._read_byte_pid(link, "010D")
                    update["vehicle"]["coolant_c"] = self._read_byte_pid(link, "0105", offset=-40)
                    voltage = self._read_voltage(link)
                    if voltage is not None:
                        update["vehicle"]["voltage_v"] = voltage
                    mil, count = self._read_mil(link)
                    update["dtc"] = {"mil": mil, "count": count}
                    if mil is not None:
                        update["warnings"] = {"check_engine": mil}
                    if time.monotonic() - last_dtc_at >= 5.0:
                        last_dtc_at = time.monotonic()
                        stored = self._read_dtcs(link, "03", "43")
                        pending = self._read_dtcs(link, "07", "47")
                        permanent = self._read_dtcs(link, "0A", "4A")
                        update["dtc"].update(
                            {
                                "stored": stored,
                                "pending": pending,
                                "permanent": permanent,
                                "count": len(stored) + len(pending),
                            }
                        )
                    update["debug"] = {
                        "obd_request": self.last_obd_request,
                        "obd_response": self.last_obd_response,
                    }
                    self.callback("obd", update)
                    time.sleep(0.5)
        except OSError as exc:
            self.callback("obd", {"vehicle": {"obd_state": f"error:{exc.__class__.__name__}"}})

    def _send(self, link: Any, command: str) -> str:
        link.write((command + "\r").encode("ascii"))
        link.flush()
        raw = link.read_until(b">", size=512).decode("ascii", errors="ignore")
        response = raw.replace("\r", "\n").replace(">", "").strip()
        self.last_obd_request = command
        self.last_obd_response = response
        return response

    def _read_byte_pid(self, link: Any, request: str, offset: int = 0) -> int | None:
        response = self._send(link, request)
        return self._parse_byte_pid_response(response, "41" + request[2:], offset=offset)

    def _read_rpm(self, link: Any) -> int | None:
        return self._parse_rpm_response(self._send(link, "010C"))

    def _read_voltage(self, link: Any) -> float | None:
        voltage = self._parse_voltage_response(self._send(link, "0142"))
        if voltage is not None:
            return voltage
        return self._parse_adapter_voltage(self._send(link, "ATRV"))

    def _read_mil(self, link: Any) -> tuple[bool | None, int | None]:
        return self._parse_mil_response(self._send(link, "0101"))

    def _read_dtcs(self, link: Any, request: str, positive_service: str) -> list[str]:
        response = self._send(link, request)
        return parse_dtc_response(response, positive_service)
