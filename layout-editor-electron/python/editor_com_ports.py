from __future__ import annotations

import re
from typing import Any, Callable, Iterable


def list_com_ports(comports: Callable[[], Iterable[Any]] | None = None) -> dict[str, Any]:
    try:
        if comports is None:
            from serial.tools import list_ports

            comports = list_ports.comports
        ports = sorted((port_record(port) for port in comports()), key=port_sort_key)
        return {"ok": True, "ports": ports, "errors": []}
    except ImportError:
        return {"ok": False, "ports": [], "errors": ["pyserial is not installed"]}
    except Exception as exc:
        return {"ok": False, "ports": [], "errors": [exception_detail("COM port scan failed", exc)]}


def port_record(port: Any) -> dict[str, Any]:
    device = text_attr(port, "device")
    description = text_attr(port, "description")
    manufacturer = text_attr(port, "manufacturer")
    product = text_attr(port, "product")
    hwid = text_attr(port, "hwid")
    record = {
        "device": device,
        "name": text_attr(port, "name") or device,
        "description": description,
        "hwid": hwid,
        "manufacturer": manufacturer,
        "product": product,
        "serialNumber": text_attr(port, "serial_number"),
        "location": text_attr(port, "location"),
        "vid": hex_attr(port, "vid"),
        "pid": hex_attr(port, "pid"),
    }
    record["likelyCanable"] = likely_canable_port(record)
    return record


def port_sort_key(port: dict[str, Any]) -> tuple[int, int, str]:
    device = str(port.get("device") or "")
    match = re.fullmatch(r"COM(\d+)", device, flags=re.IGNORECASE)
    port_number = int(match.group(1)) if match else 10000
    return (0 if port.get("likelyCanable") else 1, port_number, device)


def likely_canable_port(record: dict[str, Any]) -> bool:
    text = " ".join(str(record.get(key) or "") for key in ("device", "description", "hwid", "manufacturer", "product")).lower()
    return bool(re.search(r"\b(canable|candlelight|candle|slcan|usb to can|can adapter)\b", text))


def text_attr(port: Any, name: str) -> str:
    value = getattr(port, name, "")
    return "" if value is None else str(value)


def hex_attr(port: Any, name: str) -> str:
    value = getattr(port, name, None)
    if value in (None, ""):
        return ""
    try:
        return f"{int(value):04X}"
    except (TypeError, ValueError):
        return str(value)


def exception_detail(prefix: str, exc: Exception) -> str:
    detail = str(exc).strip()
    suffix = f"{exc.__class__.__name__}: {detail}" if detail else exc.__class__.__name__
    return f"{prefix}: {suffix}"
