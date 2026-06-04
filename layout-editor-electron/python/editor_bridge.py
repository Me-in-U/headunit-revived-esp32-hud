from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path
from typing import Any

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from editor_paths import (  # noqa: E402
    default_layout_path,
    ensure_pi_hud_path,
)

ensure_pi_hud_path()

def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    payload = read_payload()
    try:
        result = dispatch(command, payload)
    except Exception as exc:  # pragma: no cover - surfaced to Electron stderr.
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


def read_payload() -> dict[str, Any]:
    raw = sys.stdin.buffer.read().decode("utf-8").strip()
    if not raw:
        return {}
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("payload must be a JSON object")
    return data


def dispatch(command: str, payload: dict[str, Any]) -> dict[str, Any]:
    if command == "scan-obd-ble":
        from editor_vehicle_live import scan_obd_ble_devices

        return scan_obd_ble_devices(float(payload.get("timeoutSeconds", 5.0)))
    if command == "inspect-obd-ble":
        from editor_vehicle_live import inspect_obd_ble_device

        return inspect_obd_ble_device(str(payload.get("mac", "")), float(payload.get("timeoutSeconds", 5.0)))
    if command == "list-com-ports":
        from editor_com_ports import list_com_ports

        return list_com_ports()
    if command == "metadata":
        from editor_services import metadata_response

        return metadata_response()
    if command == "load-default":
        from editor_services import load_layout_response

        return load_layout_response(default_layout_path())
    if command == "load-layout":
        from editor_services import load_layout_response

        return load_layout_response(Path(str(payload["path"])))
    if command == "render-preview":
        from editor_preview import render_preview_png
        from editor_services import payload_layout, render_size

        layout = payload_layout(payload)
        width, height = render_size(layout, payload)
        state_override = payload.get("stateOverride")
        png = render_preview_png(layout, width, height, state_override if isinstance(state_override, dict) else None)
        return {"ok": True, "width": width, "height": height, "png": base64.b64encode(png).decode("ascii")}
    if command == "validate-layout":
        from editor_layout import prepare_for_screen
        from editor_services import payload_layout, verification_response
        from hud_pi.layout_verifier import verify_layout

        layout = prepare_for_screen(payload_layout(payload), str(payload.get("currentScreen", "standalone")))
        canvas = layout["canvas"]
        result = verify_layout(layout, width=canvas["width"], height=canvas["height"])
        return verification_response(result)
    if command == "save-layout":
        from editor_layout import prepare_for_save
        from editor_services import payload_layout

        output = Path(str(payload["path"]))
        layout = prepare_for_save(payload_layout(payload), str(payload.get("currentScreen", "standalone")))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(layout, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return {
            "ok": True,
            "path": str(output),
            "layout": layout,
            "message": f"Saved layout: {output}",
        }
    if command == "export-snapshot":
        from editor_layout import prepare_for_screen
        from editor_services import payload_layout, verification_response
        from hud_pi.layout_verifier import verify_layout

        layout = prepare_for_screen(payload_layout(payload), str(payload.get("currentScreen", "standalone")))
        output = Path(str(payload["output"]))
        canvas = layout["canvas"]
        result = verify_layout(layout, width=canvas["width"], height=canvas["height"], output=output)
        return verification_response(result)
    if command == "export-field-pack":
        from editor_layout import prepare_for_save
        from editor_services import export_field_pack_response, payload_layout

        output = Path(str(payload["output"]))
        layout_path = Path(str(payload.get("path") or default_layout_path()))
        layout = prepare_for_save(payload_layout(payload), str(payload.get("currentScreen", "standalone")))
        return export_field_pack_response(layout, layout_path, output)
    raise ValueError(f"unknown command: {command}")


if __name__ == "__main__":
    raise SystemExit(main())
