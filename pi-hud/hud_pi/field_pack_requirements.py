from __future__ import annotations

from pathlib import Path


def require_file(path: Path, label: str) -> None:
    if not path.is_file():
        raise ValueError(f"{label} does not exist: {path}")


def require_directory(path: Path, label: str) -> None:
    if not path.is_dir():
        raise ValueError(f"{label} does not exist: {path}")
