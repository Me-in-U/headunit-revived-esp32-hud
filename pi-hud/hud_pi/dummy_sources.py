from __future__ import annotations

import math
import time
from typing import Any

from .source_threads import SourceThread, StateCallback


def dummy_vehicle_update(elapsed: float) -> dict[str, Any]:
    speed = max(0, int(42 + 12 * math.sin(elapsed / 4)))
    rpm = int(1200 + speed * 24 + 160 * math.sin(elapsed))
    return {
        "vehicle": {
            "speed_kmh": speed,
            "rpm": rpm,
            "coolant_c": 88,
            "voltage_v": 14.1,
            "gear_range": "D",
            "source": "dummy",
            "obd_state": "dummy",
            "can_state": "dummy",
        },
        "warnings": {
            "door_open": False,
            "battery": False,
            "brake": False,
            "abs": False,
            "airbag": False,
            "oil_pressure": False,
            "check_engine": False,
            "eps": False,
            "coolant_temp": False,
            "eco": True,
        },
    }


class DummyVehicleSource(SourceThread):
    def __init__(self, callback: StateCallback) -> None:
        super().__init__(callback, "dummy-vehicle")
        self.start_time = time.monotonic()

    def run(self) -> None:
        while not self.stop_event.is_set():
            elapsed = time.monotonic() - self.start_time
            self.callback("dummy", dummy_vehicle_update(elapsed))
            time.sleep(0.25)
