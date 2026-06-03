from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .diagnostics_common import compact_response


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
