from __future__ import annotations

import asyncio
import copy
import json
import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable

from editor_paths import ensure_pi_hud_path

ensure_pi_hud_path()

from hud_pi.ble_obd_discovery import (  # noqa: E402
    characteristic_infos_from_services,
    classify_ble_obd_characteristics,
)
from hud_pi.can_signals import merge_nested_update, selected_vehicle_can_signals  # noqa: E402
from hud_pi.obd import parse_dtc_response  # noqa: E402
from hud_pi.obd_polling import Elm327PollingMixin  # noqa: E402
from hud_pi.diagnostics_common import compact_response  # noqa: E402
from hud_pi.diagnostics_obd import run_ble_elm_commands  # noqa: E402
from editor_can_analysis import can_message_to_record, summarize_can_records  # noqa: E402


EventSink = Callable[[dict[str, Any]], None]

OBD_LIVE_COMMANDS = ("ATI", "ATDP", "0100", "0101", "010C", "010D", "0105", "0142", "03", "07", "0A")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def status_event(source: str, state: str, detail: str = "") -> dict[str, Any]:
    return {
        "type": "status",
        "source": source,
        "state": state,
        "detail": detail,
        "updatedAt": utc_now(),
    }


def build_can_bus_kwargs(config: dict[str, Any]) -> dict[str, Any]:
    channel = str(config.get("channel", "")).strip()
    if not channel:
        raise ValueError("CAN channel is required")
    kwargs: dict[str, Any] = {
        "channel": channel,
        "interface": str(config.get("interface") or "slcan"),
    }
    bitrate = config.get("bitrate")
    if bitrate not in (None, ""):
        kwargs["bitrate"] = int(bitrate)
    tty_baudrate = config.get("ttyBaudrate", config.get("tty_baudrate"))
    if tty_baudrate not in (None, ""):
        kwargs["tty_baudrate"] = int(tty_baudrate)
    if "listenOnly" in config or "listen_only" in config:
        kwargs["listen_only"] = bool(config.get("listenOnly", config.get("listen_only")))
    return kwargs


def open_can_bus(can_module: Any, config: dict[str, Any]) -> Any:
    kwargs = build_can_bus_kwargs(config)
    try:
        return can_module.interface.Bus(**kwargs)
    except TypeError:
        legacy_kwargs = dict(kwargs)
        legacy_kwargs["bustype"] = legacy_kwargs.pop("interface")
        return can_module.interface.Bus(**legacy_kwargs)


def exception_detail(prefix: str, exc: Exception) -> str:
    detail = str(exc).strip()
    suffix = f"{exc.__class__.__name__}: {detail}" if detail else exc.__class__.__name__
    return f"{prefix}: {suffix}"


async def _scan_obd_ble_devices(timeout: float = 5.0) -> dict[str, Any]:
    from bleak import BleakScanner

    devices = await BleakScanner.discover(timeout=timeout)
    return {
        "ok": True,
        "devices": [
            {
                "address": str(getattr(device, "address", "")),
                "name": str(getattr(device, "name", "") or ""),
                "rssi": getattr(device, "rssi", None),
            }
            for device in devices
        ],
    }


def scan_obd_ble_devices(timeout: float = 5.0) -> dict[str, Any]:
    try:
        return asyncio.run(_scan_obd_ble_devices(timeout=timeout))
    except ImportError:
        return {"ok": False, "errors": ["bleak is not installed"], "devices": []}
    except Exception as exc:
        return {"ok": False, "errors": [exception_detail("BLE scan failed", exc)], "devices": []}


async def _inspect_obd_ble_device(mac: str, timeout: float = 5.0) -> dict[str, Any]:
    from bleak import BleakClient

    async with BleakClient(mac, timeout=timeout) as client:
        services = getattr(client, "services", None)
        if services is None:
            services = await client.get_services()
        characteristics = characteristic_infos_from_services(services)
    result = classify_ble_obd_characteristics(characteristics)
    return {
        "ok": bool(result.pairs),
        "mac": mac,
        "rxCandidates": [item.__dict__ for item in result.rx_candidates],
        "txCandidates": [item.__dict__ for item in result.tx_candidates],
        "pairs": [item.__dict__ for item in result.pairs],
        "errors": [] if result.pairs else ["No notify/write BLE characteristic pair found"],
    }


def inspect_obd_ble_device(mac: str, timeout: float = 5.0) -> dict[str, Any]:
    if not mac:
        return {"ok": False, "mac": "", "rxCandidates": [], "txCandidates": [], "pairs": [], "errors": ["BLE MAC is required"]}
    try:
        return asyncio.run(_inspect_obd_ble_device(mac, timeout=timeout))
    except ImportError:
        return {"ok": False, "mac": mac, "rxCandidates": [], "txCandidates": [], "pairs": [], "errors": ["bleak is not installed"]}
    except Exception as exc:
        return {
            "ok": False,
            "mac": mac,
            "rxCandidates": [],
            "txCandidates": [],
            "pairs": [],
            "errors": [exception_detail(f"{mac} inspect failed", exc)],
        }


class _ObdParser(Elm327PollingMixin):
    last_obd_request = ""
    last_obd_response = ""


def build_obd_live_update(records: list[dict[str, Any]]) -> dict[str, Any]:
    parser = _ObdParser()
    by_command = {str(record.get("command", "")): str(record.get("response", "")) for record in records}
    update: dict[str, Any] = {
        "vehicle": {
            "source": "windows-obd",
            "obd_state": "live",
        },
        "obd": {
            "adapter_identity": compact_response(by_command.get("ATI", "")),
            "protocol": compact_response(by_command.get("ATDP", "")),
            "supported_pid_bitmap": compact_response(by_command.get("0100", "")),
        },
        "debug": {},
    }
    if records:
        update["debug"]["obd_request"] = records[-1].get("command", "")
        update["debug"]["obd_response"] = records[-1].get("response", "")
    rpm = parser._parse_rpm_response(by_command.get("010C", ""))
    speed = parser._parse_byte_pid_response(by_command.get("010D", ""), "410D")
    coolant = parser._parse_byte_pid_response(by_command.get("0105", ""), "4105", offset=-40)
    voltage = parser._parse_voltage_response(by_command.get("0142", ""))
    mil, count = parser._parse_mil_response(by_command.get("0101", ""))
    if voltage is None:
        voltage = parser._parse_adapter_voltage(by_command.get("ATRV", ""))
    for key, value in (("rpm", rpm), ("speed_kmh", speed), ("coolant_c", coolant), ("voltage_v", voltage)):
        if value is not None:
            update["vehicle"][key] = value
    update["dtc"] = {
        "mil": mil,
        "count": count,
        "stored": parse_dtc_response(by_command.get("03", ""), "43"),
        "pending": parse_dtc_response(by_command.get("07", ""), "47"),
        "permanent": parse_dtc_response(by_command.get("0A", ""), "4A"),
    }
    update["dtc"]["count"] = len(update["dtc"]["stored"]) + len(update["dtc"]["pending"]) if update["dtc"]["stored"] or update["dtc"]["pending"] else count
    return update


class VehicleLiveSession:
    def __init__(
        self,
        config: dict[str, Any],
        *,
        emit: EventSink,
        can_bus_factory: Callable[[dict[str, Any]], Any] | None = None,
        obd_command_runner: Callable[[dict[str, Any], tuple[str, ...]], list[str]] | None = None,
    ) -> None:
        self.config = copy.deepcopy(config)
        self.emit = emit
        self.can_bus_factory = can_bus_factory or self._default_can_bus_factory
        self.obd_command_runner = obd_command_runner or self._default_obd_command_runner
        self.stop_event = threading.Event()
        self.merged_state: dict[str, Any] = {}
        self.can_records: list[dict[str, Any]] = []
        self.signal_definitions = selected_vehicle_can_signals(self.config.get("layout", {}))

    def stop(self) -> None:
        self.stop_event.set()

    def run_forever(self) -> None:
        threads: list[threading.Thread] = []
        if self.config.get("can", {}).get("enabled"):
            threads.append(threading.Thread(target=self.run_can_loop, daemon=True))
        if self.config.get("obd", {}).get("enabled"):
            threads.append(threading.Thread(target=self.run_obd_loop, daemon=True))
        if not threads:
            self.emit(status_event("can", "idle", "CAN disabled"))
            self.emit(status_event("obd", "idle", "OBD disabled"))
            return
        for thread in threads:
            thread.start()
        try:
            while any(thread.is_alive() for thread in threads) and not self.stop_event.is_set():
                time.sleep(0.1)
        finally:
            self.stop_event.set()
            for thread in threads:
                thread.join(timeout=1.0)

    def run_can_once(self) -> None:
        config = self.config.get("can", {})
        if not config.get("enabled"):
            self.emit(status_event("can", "idle", "CAN disabled"))
            return
        self.emit(status_event("can", "connecting", "Opening CANable SLCAN channel"))
        bus = self.can_bus_factory(config)
        try:
            message = bus.recv(timeout=float(config.get("timeoutSeconds", 0.5)))
            if message is None:
                self.emit(status_event("can", "stale", "No CAN frames received"))
                return
            self._process_can_message(message)
        finally:
            shutdown = getattr(bus, "shutdown", None)
            if callable(shutdown):
                shutdown()

    def run_can_loop(self) -> None:
        config = self.config.get("can", {})
        try:
            self.emit(status_event("can", "connecting", "Opening CANable SLCAN channel"))
            bus = self.can_bus_factory(config)
            self.emit(status_event("can", "live", "CANable connected"))
            try:
                while not self.stop_event.is_set():
                    message = bus.recv(timeout=0.5)
                    if message is not None:
                        self._process_can_message(message)
            finally:
                shutdown = getattr(bus, "shutdown", None)
                if callable(shutdown):
                    shutdown()
        except Exception as exc:
            self.emit(status_event("can", "error", f"{exc.__class__.__name__}: {exc}"))

    def run_obd_once(self) -> None:
        config = self.config.get("obd", {})
        if not config.get("enabled"):
            self.emit(status_event("obd", "idle", "OBD disabled"))
            return
        self.emit(status_event("obd", "connecting", "Opening BLE ELM327 adapter"))
        responses = self.obd_command_runner(config, OBD_LIVE_COMMANDS)
        records = []
        for command, response in zip(OBD_LIVE_COMMANDS, responses):
            record = {"command": command, "response": compact_response(response), "ok": bool(compact_response(response))}
            records.append(record)
            self.emit({"type": "obd_record", "source": "obd", "record": record, "updatedAt": utc_now()})
        self._emit_state("obd", build_obd_live_update(records))
        self.emit(status_event("obd", "live", "OBD BLE live"))

    def run_obd_loop(self) -> None:
        interval = max(0.5, float(self.config.get("obd", {}).get("pollSeconds", 1.5)))
        while not self.stop_event.is_set():
            try:
                self.run_obd_once()
            except Exception as exc:
                self.emit(status_event("obd", "error", f"{exc.__class__.__name__}: {exc}"))
            self.stop_event.wait(interval)

    def _process_can_message(self, message: Any) -> None:
        record = can_message_to_record(message)
        self.can_records.append(record)
        self.can_records = self.can_records[-500:]
        self.emit({"type": "can_frame", "source": "can", "record": record, "updatedAt": utc_now()})
        summary = summarize_can_records(self.can_records)
        self.emit({"type": "can_summary", "source": "can", "summary": summary, "updatedAt": utc_now()})
        update = {
            "vehicle": {"can_state": "live"},
            "debug": {"can_frame_count": len(self.can_records), "last_can_id": record["id"]},
        }
        decoded = self._decode_record(record)
        merge_nested_update(update, decoded)
        self._emit_state("can", update)
        self.emit(status_event("can", "live", f"{summary['frame_count']} frames"))

    def _decode_record(self, record: dict[str, Any]) -> dict[str, Any]:
        from hud_pi.can_signals import decode_can_signals

        try:
            frame_id = int(record["arbitration_id"])
            data = bytes(int(part, 16) for part in str(record["data"]).split())
        except (KeyError, TypeError, ValueError):
            return {}
        return decode_can_signals(frame_id, data, self.signal_definitions)

    def _emit_state(self, source: str, update: dict[str, Any]) -> None:
        merge_nested_update(self.merged_state, copy.deepcopy(update))
        self.emit(
            {
                "type": "state",
                "source": source,
                "update": update,
                "mergedState": copy.deepcopy(self.merged_state),
                "updatedAt": utc_now(),
            }
        )

    def _default_can_bus_factory(self, config: dict[str, Any]) -> Any:
        import can

        return open_can_bus(can, config)

    def _default_obd_command_runner(self, config: dict[str, Any], commands: tuple[str, ...]) -> list[str]:
        return run_ble_elm_commands(
            str(config.get("mac", "")),
            str(config.get("rxUuid") or config.get("rx_uuid") or ""),
            str(config.get("txUuid") or config.get("tx_uuid") or ""),
            list(commands),
            timeout=float(config.get("timeoutSeconds", 2.0)),
        )


def run_worker(config: dict[str, Any], emit: EventSink | None = None) -> None:
    sink = emit or (lambda event: print(json.dumps(event, ensure_ascii=False), flush=True))
    VehicleLiveSession(config, emit=sink).run_forever()
