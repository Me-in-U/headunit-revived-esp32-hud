from __future__ import annotations

import json
import os
import re
import subprocess
from typing import Any, Callable, Iterable


def list_com_ports(
    comports: Callable[[], Iterable[Any]] | None = None,
    windows_port_records: Callable[[], Iterable[dict[str, Any]]] | None = None,
    windows_registry_records: Callable[[], Iterable[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    records: list[dict[str, Any]] = []
    use_real_comports = comports is None
    try:
        if comports is None:
            from serial.tools import list_ports

            comports = list_ports.comports
        records.extend(port_record(port) for port in comports())
    except ImportError:
        errors.append("pyserial is not installed")
    except Exception as exc:
        errors.append(exception_detail("COM port scan failed", exc))

    if windows_registry_records is not None or (use_real_comports and os.name == "nt"):
        try:
            reader = windows_registry_records or list_windows_registry_serial_records
            records.extend(reader())
        except Exception as exc:
            errors.append(exception_detail("Windows registry COM port scan failed", exc))

    needs_windows_pnp = not any(record.get("likelyCanable") for record in records)
    if windows_port_records is not None or (os.name == "nt" and (not records or needs_windows_pnp)):
        try:
            reader = windows_port_records or list_windows_pnp_port_records
            records.extend(reader())
        except Exception as exc:
            errors.append(exception_detail("Windows COM port scan failed", exc))

    ports = sorted(merge_port_records(records), key=port_sort_key)
    return {"ok": bool(ports) or not errors, "ports": ports, "errors": [] if ports else errors}


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
    record["likelyObdSerial"] = likely_obd_serial_port(record)
    return record


def port_sort_key(port: dict[str, Any]) -> tuple[int, int, str]:
    device = str(port.get("device") or "")
    match = re.fullmatch(r"COM(\d+)", device, flags=re.IGNORECASE)
    port_number = int(match.group(1)) if match else 10000
    return (0 if port.get("likelyCanable") else 1, port_number, device)


def likely_canable_port(record: dict[str, Any]) -> bool:
    text = " ".join(str(record.get(key) or "") for key in ("device", "description", "hwid", "manufacturer", "product")).lower()
    return bool(re.search(r"\b(cantact|canable|candlelight|candle|slcan|usb to can|can adapter)\b", text))


def likely_obd_serial_port(record: dict[str, Any]) -> bool:
    if record.get("likelyCanable"):
        return False
    text = " ".join(str(record.get(key) or "") for key in ("device", "description", "hwid", "manufacturer", "product")).lower()
    if "000000000000_" in text or "localmfg&0000" in text:
        return False
    if "bluetooth" in text or "bthenum" in text:
        return True
    return bool(re.search(r"\b(elm327|vlink|v-link|icar|obd)\b", text))


def merge_port_records(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for record in records:
        device = str(record.get("device") or "").strip()
        if not device:
            continue
        key = device.upper()
        existing = merged.get(key)
        if existing is None:
            merged[key] = normalized_port_flags(dict(record))
            continue
        combined = dict(existing)
        for field, value in record.items():
            if field in {"likelyCanable", "likelyObdSerial"}:
                continue
            if value and (not combined.get(field) or should_replace_port_field(field, combined.get(field), value)):
                combined[field] = value
        merged[key] = normalized_port_flags(combined)
    return list(merged.values())


def normalized_port_flags(record: dict[str, Any]) -> dict[str, Any]:
    record["likelyCanable"] = likely_canable_port(record)
    record["likelyObdSerial"] = likely_obd_serial_port(record)
    return record


def should_replace_port_field(field: str, existing: Any, value: Any) -> bool:
    existing_text = str(existing or "")
    value_text = str(value or "")
    if field == "hwid" and existing_text.startswith("\\Device\\") and value_text:
        return True
    if field in {"description", "product"}:
        generic = {"serial port", "bluetooth serial port"}
        return existing_text.strip().lower() in generic and value_text.strip().lower() not in generic
    return False


def list_windows_pnp_port_records() -> list[dict[str, Any]]:
    script = (
        "[Console]::OutputEncoding=[Text.Encoding]::UTF8; "
        "Get-CimInstance Win32_PnPEntity | "
        "Where-Object { $_.Name -match '\\(COM\\d+\\)' } | "
        "Select-Object Status,@{Name='FriendlyName';Expression={$_.Name}},@{Name='InstanceId';Expression={$_.PNPDeviceID}} | "
        "ConvertTo-Json -Depth 3 -Compress"
    )
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", script],
        check=False,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=6,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(detail or f"PowerShell exited {result.returncode}")
    output = result.stdout.strip()
    if not output:
        return []
    data = json.loads(output)
    items = data if isinstance(data, list) else [data]
    return [windows_pnp_port_record(item) for item in items if isinstance(item, dict)]


def list_windows_registry_serial_records() -> list[dict[str, Any]]:
    import winreg

    records: list[dict[str, Any]] = []
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DEVICEMAP\SERIALCOMM") as key:
      index = 0
      while True:
          try:
              registry_name, device, _kind = winreg.EnumValue(key, index)
          except OSError:
              break
          records.append(windows_registry_serial_record(str(registry_name), str(device)))
          index += 1
    return records


def windows_registry_serial_record(registry_name: str, device: str) -> dict[str, Any]:
    device = device.strip().upper()
    is_bluetooth = "bth" in registry_name.lower() or "bluetooth" in registry_name.lower()
    description = "Bluetooth serial port" if is_bluetooth else "Serial port"
    record = {
        "device": device,
        "name": device,
        "description": description,
        "hwid": registry_name,
        "manufacturer": "Microsoft" if is_bluetooth else "",
        "product": description if is_bluetooth else "",
        "serialNumber": "",
        "location": "",
        "vid": "",
        "pid": "",
        "status": "",
    }
    record["likelyCanable"] = likely_canable_port(record)
    record["likelyObdSerial"] = likely_obd_serial_port(record)
    return record


def windows_pnp_port_record(item: dict[str, Any]) -> dict[str, Any]:
    friendly = str(item.get("FriendlyName") or "")
    instance_id = str(item.get("InstanceId") or "")
    device_match = re.search(r"\((COM\d+)\)", friendly, flags=re.IGNORECASE)
    device = device_match.group(1).upper() if device_match else ""
    description = re.sub(r"\s*\(COM\d+\)\s*$", "", friendly, flags=re.IGNORECASE).strip()
    record = {
        "device": device,
        "name": device,
        "description": description,
        "hwid": instance_id,
        "manufacturer": "",
        "product": description,
        "serialNumber": serial_from_instance_id(instance_id),
        "location": "",
        "vid": id_from_instance_id(instance_id, "VID"),
        "pid": id_from_instance_id(instance_id, "PID"),
        "status": str(item.get("Status") or ""),
    }
    record["likelyCanable"] = likely_canable_port(record)
    record["likelyObdSerial"] = likely_obd_serial_port(record)
    return record


def id_from_instance_id(instance_id: str, key: str) -> str:
    match = re.search(rf"{re.escape(key)}[_&]([0-9A-F]{{4}})", instance_id, flags=re.IGNORECASE)
    return match.group(1).upper() if match else ""


def serial_from_instance_id(instance_id: str) -> str:
    parts = [part for part in re.split(r"[\\\/]", instance_id) if part]
    return parts[-1] if len(parts) >= 3 else ""


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
