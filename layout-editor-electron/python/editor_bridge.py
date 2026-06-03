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

from editor_layout import prepare_for_save, prepare_for_screen  # noqa: E402
from hud_pi.layout_verifier import verify_layout  # noqa: E402
from editor_preview import render_preview_png  # noqa: E402
from editor_services import (  # noqa: E402
    export_field_pack_response,
    load_layout_response,
    metadata_response,
    payload_layout,
    render_size,
    verification_response,
)

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
    if command == "metadata":
        return metadata_response()
    if command == "load-default":
        return load_layout_response(default_layout_path())
    if command == "load-layout":
        return load_layout_response(Path(str(payload["path"])))
    if command == "render-preview":
        layout = payload_layout(payload)
        width, height = render_size(layout, payload)
        png = render_preview_png(layout, width, height)
        return {"ok": True, "width": width, "height": height, "png": base64.b64encode(png).decode("ascii")}
    if command == "validate-layout":
        layout = prepare_for_screen(payload_layout(payload), str(payload.get("currentScreen", "standalone")))
        canvas = layout["canvas"]
        result = verify_layout(layout, width=canvas["width"], height=canvas["height"])
        return verification_response(result)
    if command == "save-layout":
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
        layout = prepare_for_screen(payload_layout(payload), str(payload.get("currentScreen", "standalone")))
        output = Path(str(payload["output"]))
        canvas = layout["canvas"]
        result = verify_layout(layout, width=canvas["width"], height=canvas["height"], output=output)
        return verification_response(result)
    if command == "export-field-pack":
        output = Path(str(payload["output"]))
        layout_path = Path(str(payload.get("path") or default_layout_path()))
        layout = prepare_for_save(payload_layout(payload), str(payload.get("currentScreen", "standalone")))
        return export_field_pack_response(layout, layout_path, output)
    raise ValueError(f"unknown command: {command}")


if __name__ == "__main__":
    raise SystemExit(main())
