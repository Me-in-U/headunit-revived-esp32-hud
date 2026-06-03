from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FieldPackResult:
    output: Path
    render_size: tuple[int, int]
    non_background_pixels: int
    manifest: dict[str, Any]
