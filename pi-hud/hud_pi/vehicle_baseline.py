from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from .diagnostics import compact_response

OBD_BASELINE_COMMANDS = [
    "ATI",
    "AT@1",
    "ATDP",
    "ATDPN",
    "ATRV",
    "ATH1",
    "0100",
    "0120",
    "0140",
    "0160",
    "0101",
    "010C",
    "010D",
    "0105",
    "0142",
    "0902",
    "03",
    "07",
    "0A",
]

ELM_FAILURE_MARKERS = (
    "NO DATA",
    "UNABLE",
    "ERROR",
    "STOPPED",
    "BUS INIT",
    "CAN ERROR",
    "?",
)


def response_ok(response: str) -> bool:
    cleaned = compact_response(response).strip()
    if not cleaned:
        return False
    upper = cleaned.upper()
    return not any(marker in upper for marker in ELM_FAILURE_MARKERS)


def collect_obd_baseline(send_command: Callable[[str], str], commands: list[str] | tuple[str, ...] = OBD_BASELINE_COMMANDS) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for command in commands:
        try:
            response = compact_response(send_command(command))
            ok = response_ok(response)
            error = ""
        except Exception as exc:
            response = ""
            ok = False
            error = exc.__class__.__name__
        record: dict[str, Any] = {
            "command": command,
            "response": response,
            "ok": ok,
        }
        if error:
            record["error"] = error
        records.append(record)
    return records


def profile_obd_probe_commands(profile: dict[str, Any]) -> list[str]:
    commands: list[str] = []
    for entry in profile.get("obd_probe_commands", []):
        if isinstance(entry, str):
            command = entry.strip()
            if command:
                commands.append(command)
            continue
        if not isinstance(entry, dict) or entry.get("enabled", True) is False:
            continue
        for command in entry.get("commands", []):
            if not isinstance(command, str):
                continue
            cleaned = command.strip()
            if cleaned:
                commands.append(cleaned)
    return commands


def build_obd_baseline_commands(profile: dict[str, Any] | None = None) -> list[str]:
    return list(OBD_BASELINE_COMMANDS) + profile_obd_probe_commands(profile or {})


def can_message_to_record(message: Any) -> dict[str, Any]:
    arbitration_id = int(message.arbitration_id)
    data = bytes(message.data)
    return {
        "timestamp": getattr(message, "timestamp", None),
        "arbitration_id": arbitration_id,
        "id": f"0x{arbitration_id:X}",
        "extended": bool(getattr(message, "is_extended_id", False)),
        "dlc": int(getattr(message, "dlc", len(data))),
        "data": " ".join(f"{byte:02X}" for byte in data),
    }


def collect_can_frames(
    recv: Callable[[float], Any],
    duration_seconds: float = 10.0,
    max_frames: int = 500,
    now: Callable[[], float] = time.monotonic,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    deadline = now() + max(0.0, duration_seconds)
    while len(records) < max(0, max_frames) and now() <= deadline:
        remaining = max(0.0, deadline - now())
        message = recv(min(0.5, remaining))
        if message is None:
            if remaining <= 0:
                break
            continue
        records.append(can_message_to_record(message))
    return records


def summarize_can_records(records: list[dict[str, Any]], sample_limit: int = 3) -> dict[str, Any]:
    grouped: dict[int, list[dict[str, Any]]] = {}
    for record in records:
        arbitration_id = _record_arbitration_id(record)
        if arbitration_id is None:
            continue
        grouped.setdefault(arbitration_id, []).append(record)

    summaries = []
    for arbitration_id, group in sorted(grouped.items(), key=lambda item: item[0]):
        payloads = [_parse_data_bytes(record.get("data", "")) for record in group]
        payloads = [payload for payload in payloads if payload is not None]
        summaries.append(
            {
                "id": f"0x{arbitration_id:X}",
                "arbitration_id": arbitration_id,
                "count": len(group),
                "dlc": _most_common_int([record.get("dlc") for record in group], fallback=len(payloads[0]) if payloads else 0),
                "first_timestamp": group[0].get("timestamp"),
                "last_timestamp": group[-1].get("timestamp"),
                "changing_byte_indexes": _changing_byte_indexes(payloads),
                "sample_data": _sample_unique_payloads(group, sample_limit),
            }
        )
    return {
        "frame_count": len(records),
        "summarized_frame_count": sum(item["count"] for item in summaries),
        "unique_id_count": len(summaries),
        "ids": summaries,
    }


def _record_arbitration_id(record: dict[str, Any]) -> int | None:
    raw_id = record.get("arbitration_id")
    try:
        return int(raw_id)
    except (TypeError, ValueError):
        id_text = str(record.get("id", "")).strip()
        if not id_text:
            return None
        try:
            return int(id_text, 16)
        except ValueError:
            return None


def _parse_data_bytes(data: Any) -> list[int] | None:
    if not isinstance(data, str):
        return None
    try:
        return [int(part, 16) for part in data.split()]
    except ValueError:
        return None


def _changing_byte_indexes(payloads: list[list[int]]) -> list[int]:
    if len(payloads) < 2:
        return []
    max_len = max(len(payload) for payload in payloads)
    changing = []
    for index in range(max_len):
        values = {payload[index] if index < len(payload) else None for payload in payloads}
        if len(values) > 1:
            changing.append(index)
    return changing


def _sample_unique_payloads(records: list[dict[str, Any]], limit: int) -> list[str]:
    samples: list[str] = []
    seen: set[str] = set()
    for record in records:
        data = str(record.get("data", "")).strip()
        if not data or data in seen:
            continue
        seen.add(data)
        samples.append(data)
        if len(samples) >= max(1, limit):
            break
    return samples


def _most_common_int(values: list[Any], fallback: int) -> int:
    counts: dict[int, int] = {}
    for value in values:
        try:
            normalized = int(value)
        except (TypeError, ValueError):
            continue
        counts[normalized] = counts.get(normalized, 0) + 1
    if not counts:
        return fallback
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
