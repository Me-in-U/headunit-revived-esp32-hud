from __future__ import annotations

from pathlib import Path

from .diagnostics_can import open_socketcan_bus, probe_can
from .diagnostics_common import DiagnosticResult, compact_response, format_result, load_env_file
from .diagnostics_display import parse_framebuffer_virtual_size, probe_display
from .diagnostics_obd import probe_obd, probe_obd_ble, run_ble_elm_commands, send_elm_command
from .layout import load_layout
from .layout_verifier import verify_layout_file


def layout_summary(path: str | Path, width: int = 1920, height: int = 480, require_handoff: bool = False) -> DiagnosticResult:
    try:
        layout = load_layout(path)
    except OSError as exc:
        return DiagnosticResult("layout", False, f"cannot open: {exc}")
    except ValueError as exc:
        return DiagnosticResult("layout", False, f"invalid json: {exc}")

    canvas = layout.get("canvas", {})
    canvas_width = canvas.get("width", width)
    canvas_height = canvas.get("height", height)
    elements = layout.get("elements", [])
    vehicle = layout.get("selected_vehicle", "unknown")
    result = verify_layout_file(path, width=width, height=height, require_handoff=require_handoff)
    if not result.ok:
        return DiagnosticResult("layout", False, "; ".join(result.errors))
    return DiagnosticResult("layout", True, f"{canvas_width}x{canvas_height}, elements={len(elements)}, vehicle={vehicle}")
