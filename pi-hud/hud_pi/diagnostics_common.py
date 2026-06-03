from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import MutableMapping


@dataclass(frozen=True)
class DiagnosticResult:
    name: str
    ok: bool
    detail: str


def format_result(result: DiagnosticResult) -> str:
    marker = "OK" if result.ok else "FAIL"
    return f"[{marker}] {result.name}: {result.detail}"


def load_env_file(path: str | Path, environ: MutableMapping[str, str], override: bool = False) -> list[str]:
    env_path = Path(path)
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []

    loaded: list[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        if key in environ and not override:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        environ[key] = value
        loaded.append(key)
    return loaded


def compact_response(response: str) -> str:
    return " ".join(part.strip() for part in response.splitlines() if part.strip())
