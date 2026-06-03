from __future__ import annotations

from pathlib import Path

from .diagnostics_common import DiagnosticResult


def probe_display(width: int = 1920, height: int = 480, framebuffer_virtual_size: str | Path = "/sys/class/graphics/fb0/virtual_size") -> DiagnosticResult:
    fb_path = Path(framebuffer_virtual_size)
    try:
        raw = fb_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        return DiagnosticResult("display", False, f"cannot read {fb_path}: {exc.__class__.__name__}")

    try:
        actual_width, actual_height = parse_framebuffer_virtual_size(raw)
    except ValueError as exc:
        return DiagnosticResult("display", False, f"invalid framebuffer size {raw!r}: {exc}")

    if actual_width != width or actual_height != height:
        return DiagnosticResult("display", False, f"framebuffer={actual_width}x{actual_height}, expected {width}x{height}")
    return DiagnosticResult("display", True, f"framebuffer={actual_width}x{actual_height}")


def parse_framebuffer_virtual_size(value: str) -> tuple[int, int]:
    normalized = value.strip().replace("x", ",").replace(" ", ",")
    parts = [part for part in normalized.split(",") if part]
    if len(parts) != 2:
        raise ValueError("expected WIDTH,HEIGHT")
    width, height = (int(part) for part in parts)
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    return width, height
