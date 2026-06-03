from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
import sys
import tempfile
import zipfile
from io import BytesIO
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[2]
PI_HUD_PATH = REPO_ROOT / "pi-hud"
if PI_HUD_PATH.exists() and str(PI_HUD_PATH) not in sys.path:
    sys.path.insert(0, str(PI_HUD_PATH))

import pygame  # noqa: E402
from hud_pi.layout import normalize_layout_for_save  # noqa: E402
from hud_pi.layout_verifier import build_layout_handoff, verify_layout  # noqa: E402
from hud_pi.renderer import HudRenderer  # noqa: E402
from hud_pi.state import HudState  # noqa: E402
from hud_pi.vehicle_profiles import load_vehicle_profiles, profile_map  # noqa: E402

DEFAULT_LAYOUT_NAME = "avante_hd_2010_default.json"

PALETTE: dict[str, list[dict[str, Any]]] = {
    "Speed": [
        {
            "type": "value",
            "label": "Speed",
            "binding": "vehicle.speed_kmh",
            "fallback_bindings": ["vehicle.speed_kmh_backup"],
            "value_style": "digital",
            "min_value": 0,
            "max_value": 220,
            "prefix": "",
            "suffix": "",
            "font_size": 120,
        },
        {
            "type": "value",
            "label": "Speed bar",
            "binding": "vehicle.speed_kmh",
            "fallback_bindings": ["vehicle.speed_kmh_backup"],
            "value_style": "bar",
            "min_value": 0,
            "max_value": 220,
            "prefix": "",
            "suffix": " km/h",
            "font_size": 32,
            "accent": "#24d36b",
            "inactive_color": "#1a2430",
        },
        {
            "type": "value",
            "label": "Speed needle",
            "binding": "vehicle.speed_kmh",
            "fallback_bindings": ["vehicle.speed_kmh_backup"],
            "value_style": "needle",
            "min_value": 0,
            "max_value": 220,
            "tick_interval": 20,
            "prefix": "",
            "suffix": " km/h",
            "font_size": 30,
            "accent": "#24d36b",
            "inactive_color": "#1a2430",
        },
        {
            "type": "value",
            "label": "Speed analog",
            "binding": "vehicle.speed_kmh",
            "fallback_bindings": ["vehicle.speed_kmh_backup"],
            "value_style": "analog",
            "min_value": 0,
            "max_value": 220,
            "tick_interval": 20,
            "prefix": "",
            "suffix": " km/h",
            "font_size": 30,
            "accent": "#24d36b",
            "inactive_color": "#1a2430",
        },
    ],
    "Gear": [
        {
            "type": "gear_indicator",
            "label": "Gear strip",
            "binding": "vehicle.gear_range",
            "gears": ["P", "R", "N", "D", "3", "2", "L"],
            "gear_style": "strip",
            "font_size": 28,
            "active_font_size": 92,
            "accent": "#24d36b",
            "inactive_color": "#4a5568",
        },
        {
            "type": "gear_indicator",
            "label": "Gear active",
            "binding": "vehicle.gear_range",
            "gears": ["P", "R", "N", "D", "3", "2", "L"],
            "gear_style": "active_only",
            "font_size": 36,
            "active_font_size": 118,
            "accent": "#24d36b",
            "inactive_color": "#4a5568",
        },
    ],
    "RPM": [
        {
            "type": "value",
            "label": "RPM",
            "binding": "vehicle.rpm",
            "value_style": "digital",
            "min_value": 0,
            "max_value": 8000,
            "prefix": "RPM ",
            "suffix": "",
            "font_size": 36,
        },
        {
            "type": "value",
            "label": "RPM sport",
            "binding": "vehicle.rpm",
            "value_style": "sport_gauge",
            "min_value": 0,
            "max_value": 8000,
            "tick_interval": 1000,
            "prefix": "",
            "suffix": " rpm",
            "font_size": 40,
            "accent": "#24d36b",
            "redline_color": "#ff3b30",
            "inactive_color": "#1a2430",
        },
    ],
    "Temperature": [
        {"type": "value", "label": "Coolant", "binding": "vehicle.coolant_c", "value_style": "digital", "min_value": -40, "max_value": 130, "suffix": "°C", "font_size": 32},
        {"type": "value", "label": "ATF", "binding": "vehicle.atf_c", "value_style": "digital", "min_value": -40, "max_value": 160, "prefix": "ATF ", "suffix": "°C", "font_size": 30},
    ],
    "Power/Fuel": [
        {"type": "value", "label": "Voltage", "binding": "vehicle.voltage_v", "value_style": "digital", "min_value": 0, "max_value": 16, "suffix": "V", "font_size": 32},
        {"type": "value", "label": "Fuel", "binding": "vehicle.fuel_percent", "value_style": "bar", "min_value": 0, "max_value": 100, "prefix": "Fuel ", "suffix": "%", "font_size": 32},
        {"type": "value", "label": "Fuel value", "binding": "vehicle.fuel_percent", "value_style": "digital", "min_value": 0, "max_value": 100, "prefix": "FUEL ", "suffix": "%", "font_size": 28},
    ],
    "Driver Input": [
        {"type": "value", "label": "Backup speed", "binding": "vehicle.speed_kmh_backup", "value_style": "digital", "min_value": 0, "max_value": 220, "prefix": "GPS ", "suffix": " km/h", "font_size": 30},
        {"type": "value", "label": "Actual gear", "binding": "vehicle.gear_actual", "prefix": "G ", "font_size": 30},
        {"type": "value", "label": "Pedal", "binding": "vehicle.pedal_percent", "value_style": "bar", "min_value": 0, "max_value": 100, "prefix": "PED ", "suffix": "%", "font_size": 30},
    ],
    "Navigation": [
        {"type": "nav_icon", "label": "Turn icon", "event_binding": "nav.event_type", "side_binding": "nav.turn_side", "font_size": 32},
        {"type": "value", "label": "Instruction", "binding": "nav.instruction", "font_size": 32},
        {"type": "value", "label": "Road", "binding": "nav.road", "font_size": 30},
        {"type": "value", "label": "Next distance", "binding": "nav.distance_meters", "suffix": " m", "font_size": 28},
        {"type": "value", "label": "Nav state", "binding": "nav.connected", "prefix": "NAV ", "font_size": 28},
    ],
    "Warning Lamps": [
        {"type": "warning_icon", "label": "Door open", "binding": "warnings.door_open", "icon": "door_open", "font_size": 22},
        {"type": "warning_icon", "label": "Battery", "binding": "warnings.battery", "icon": "battery", "font_size": 22},
        {"type": "warning_icon", "label": "Brake", "binding": "warnings.brake", "icon": "brake", "font_size": 22},
        {"type": "warning_icon", "label": "ABS", "binding": "warnings.abs", "icon": "abs", "font_size": 22},
        {"type": "warning_icon", "label": "Airbag", "binding": "warnings.airbag", "icon": "airbag", "font_size": 22},
        {"type": "warning_icon", "label": "Oil", "binding": "warnings.oil_pressure", "icon": "oil_pressure", "font_size": 22},
        {"type": "warning_icon", "label": "Check engine", "binding": "warnings.check_engine", "icon": "check_engine", "font_size": 22},
        {"type": "warning_icon", "label": "EPS", "binding": "warnings.eps", "icon": "eps", "font_size": 22},
        {"type": "warning_icon", "label": "Coolant", "binding": "warnings.coolant_temp", "icon": "coolant_temp", "font_size": 22},
        {"type": "warning_icon", "label": "Seatbelt", "binding": "warnings.seatbelt", "icon": "seatbelt", "font_size": 22},
        {"type": "warning_icon", "label": "Low fuel", "binding": "warnings.low_fuel", "icon": "low_fuel", "font_size": 22},
        {"type": "warning_icon", "label": "Tire pressure", "binding": "warnings.tire_pressure", "icon": "tire_pressure", "font_size": 22},
        {"type": "warning_icon", "label": "High beam", "binding": "warnings.high_beam", "icon": "high_beam", "font_size": 22},
        {"type": "warning_icon", "label": "Low beam", "binding": "warnings.low_beam", "icon": "low_beam", "font_size": 22},
        {"type": "warning_icon", "label": "Parking lights", "binding": "warnings.parking_lights", "icon": "parking_lights", "font_size": 22},
        {"type": "warning_icon", "label": "Fog light", "binding": "warnings.fog_light", "icon": "fog_light", "font_size": 22},
        {"type": "warning_icon", "label": "Washer fluid", "binding": "warnings.washer_fluid", "icon": "washer_fluid", "font_size": 22},
        {"type": "warning_icon", "label": "Cruise control", "binding": "warnings.cruise_control", "icon": "cruise_control", "font_size": 22},
        {"type": "warning_icon", "label": "Traction control", "binding": "warnings.traction_control", "icon": "traction_control", "font_size": 22},
        {"type": "warning_icon", "label": "Glow plug", "binding": "warnings.glow_plug", "icon": "glow_plug", "font_size": 22},
    ],
    "DTC": [
        {"type": "value", "label": "DTC count", "binding": "dtc.count", "prefix": "DTC ", "font_size": 30},
        {"type": "value", "label": "MIL", "binding": "dtc.mil", "prefix": "MIL ", "font_size": 30},
    ],
    "Weather": [
        {"type": "value", "label": "Weather temp", "binding": "weather.temp_c", "suffix": "°C", "font_size": 34},
        {"type": "value", "label": "Feels like", "binding": "weather.apparent_c", "prefix": "FEELS ", "suffix": "°C", "font_size": 28},
        {"type": "value", "label": "Weather condition", "binding": "weather.condition_ko", "fallback_bindings": ["weather.condition"], "font_size": 28},
        {"type": "value", "label": "Weather wind", "binding": "weather.wind_kmh", "prefix": "WIND ", "suffix": " km/h", "font_size": 26},
        {"type": "value", "label": "Weather location", "binding": "weather.location_name", "font_size": 24},
    ],
    "Input Diagnostics": [
        {"type": "value", "label": "Vehicle source", "binding": "vehicle.source", "prefix": "SRC ", "font_size": 28},
        {"type": "value", "label": "OBD state", "binding": "vehicle.obd_state", "prefix": "OBD ", "font_size": 28},
        {"type": "value", "label": "CAN state", "binding": "vehicle.can_state", "prefix": "CAN ", "font_size": 28},
        {"type": "value", "label": "CAN frames", "binding": "debug.can_frame_count", "prefix": "CAN #", "font_size": 28},
        {"type": "value", "label": "Last CAN ID", "binding": "debug.last_can_id", "prefix": "ID ", "font_size": 28},
        {"type": "value", "label": "OBD request", "binding": "debug.obd_request", "prefix": "REQ ", "font_size": 26},
        {"type": "value", "label": "OBD response", "binding": "debug.obd_response", "prefix": "RESP ", "font_size": 24},
        {"type": "value", "label": "Stored DTC", "binding": "dtc.stored", "prefix": "STORED ", "font_size": 26},
        {"type": "value", "label": "Pending DTC", "binding": "dtc.pending", "prefix": "PENDING ", "font_size": 26},
        {"type": "value", "label": "Permanent DTC", "binding": "dtc.permanent", "prefix": "PERM ", "font_size": 26},
    ],
    "Labels": [
        {"type": "text", "label": "Text label", "text": "LABEL", "font_size": 32},
    ],
}


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


def bundled_root() -> Path:
    return REPO_ROOT


def default_layout_path() -> Path:
    env_layout = os.environ.get("HEADUNIT_HUD_LAYOUT")
    if env_layout:
        return Path(env_layout)
    candidates = [
        bundled_root() / "layouts" / DEFAULT_LAYOUT_NAME,
        REPO_ROOT / "layouts" / DEFAULT_LAYOUT_NAME,
        Path.cwd() / "layouts" / DEFAULT_LAYOUT_NAME,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def default_vehicle_profile_paths() -> list[Path]:
    candidates = [
        bundled_root() / "vehicles",
        REPO_ROOT / "vehicles",
        Path.cwd() / "vehicles",
    ]
    return [candidate for candidate in candidates if candidate.exists()]


def default_env_example_path() -> Path:
    candidates = [
        bundled_root() / "pi-hud" / "config" / "pi-hud.env.example",
        REPO_ROOT / "pi-hud" / "config" / "pi-hud.env.example",
        Path.cwd() / "pi-hud" / "config" / "pi-hud.env.example",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def default_warning_icon_assets_dir() -> Path:
    candidates = [
        bundled_root() / "pi-hud" / "assets" / "warning-icons",
        REPO_ROOT / "pi-hud" / "assets" / "warning-icons",
        Path.cwd() / "pi-hud" / "assets" / "warning-icons",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def default_nav_icon_assets_dir() -> Path:
    candidates = [
        bundled_root() / "pi-hud" / "assets" / "nav-icons",
        REPO_ROOT / "pi-hud" / "assets" / "nav-icons",
        Path.cwd() / "pi-hud" / "assets" / "nav-icons",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def render_preview_png(layout: dict[str, Any], width: int, height: int) -> bytes:
    pygame.font.init()
    preview_layout = copy.deepcopy(layout)
    preview_layout.pop("screens", None)
    state = HudState.from_layout(preview_layout)
    warnings = state.values.setdefault("warnings", {})
    for element in preview_layout.get("elements", []):
        if not isinstance(element, dict) or element.get("type") != "warning_icon":
            continue
        binding = str(element.get("binding", "")).strip()
        if binding.startswith("warnings."):
            warnings[binding.split(".", 1)[1]] = True
    surface = pygame.Surface((width, height))
    HudRenderer(preview_layout, surface).render(state)
    buffer = BytesIO()
    pygame.image.save(surface, buffer, "preview.png")
    return buffer.getvalue()


def dispatch(command: str, payload: dict[str, Any]) -> dict[str, Any]:
    if command == "metadata":
        return metadata()
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
        return export_field_pack(layout, layout_path, output)
    raise ValueError(f"unknown command: {command}")


def metadata() -> dict[str, Any]:
    profiles = profile_map(load_vehicle_profiles(default_vehicle_profile_paths()), {})
    return {
        "ok": True,
        "repoRoot": str(REPO_ROOT),
        "defaultLayoutPath": str(default_layout_path()),
        "palette": PALETTE,
        "vehicles": sorted(profiles),
        "vehicleProfiles": profiles,
    }


def load_layout_response(path: Path) -> dict[str, Any]:
    layout = json.loads(path.read_text(encoding="utf-8"))
    layout = normalize_layout_for_save(layout)
    current_screen = "standalone"
    ensure_screen_layout(layout, current_screen)
    profiles = profile_map(load_vehicle_profiles(default_vehicle_profile_paths()), layout)
    return {
        "ok": True,
        "path": str(path),
        "layout": layout,
        "currentScreen": current_screen,
        "vehicles": sorted(profiles),
        "vehicleProfiles": profiles,
    }


def payload_layout(payload: dict[str, Any]) -> dict[str, Any]:
    layout = payload.get("layout")
    if not isinstance(layout, dict):
        raise ValueError("payload.layout must be an object")
    return copy.deepcopy(layout)


def render_size(layout: dict[str, Any], payload: dict[str, Any]) -> tuple[int, int]:
    canvas = layout.setdefault("canvas", {})
    width = int(payload.get("width") or canvas.get("width") or 1920)
    height = int(payload.get("height") or canvas.get("height") or 480)
    return max(1, width), max(1, height)


def ensure_screen_layout(layout: dict[str, Any], current_screen: str) -> None:
    screens = layout.setdefault("screens", {})
    if not isinstance(screens, dict):
        screens = {}
        layout["screens"] = screens
    base_elements = copy.deepcopy(layout.get("elements", []))
    for screen_name, label in (("standalone", "Standalone vehicle HUD"), ("bridge", "Bridge navigation HUD")):
        screen = screens.setdefault(screen_name, {"label": label, "elements": copy.deepcopy(base_elements)})
        if not isinstance(screen, dict):
            screens[screen_name] = {"label": label, "elements": copy.deepcopy(base_elements)}
            screen = screens[screen_name]
        if not isinstance(screen.get("elements"), list):
            screen["elements"] = copy.deepcopy(base_elements)
    if current_screen not in screens:
        current_screen = "standalone"
    layout["elements"] = copy.deepcopy(screens[current_screen]["elements"])


def sync_current_screen(layout: dict[str, Any], current_screen: str) -> None:
    screens = layout.get("screens")
    if not isinstance(screens, dict):
        screens = {}
        layout["screens"] = screens
    if current_screen not in screens or not isinstance(screens.get(current_screen), dict):
        screens[current_screen] = {"label": current_screen.title(), "elements": []}
    screens[current_screen]["elements"] = copy.deepcopy(layout.get("elements", []))


def prepare_for_screen(layout: dict[str, Any], current_screen: str) -> dict[str, Any]:
    sync_current_screen(layout, current_screen)
    return normalize_layout_for_save(layout)


def prepare_for_save(layout: dict[str, Any], current_screen: str) -> dict[str, Any]:
    prepared = prepare_for_screen(layout, current_screen)
    canvas = prepared["canvas"]
    result = verify_layout(prepared, width=canvas["width"], height=canvas["height"])
    if not result.ok:
        raise ValueError("\n".join(result.errors))
    prepared["pi_hud_handoff"] = build_layout_handoff(prepared, result.render_size, result.non_background_pixels)
    return prepared


def verification_response(result: Any) -> dict[str, Any]:
    return {
        "ok": bool(result.ok),
        "errors": list(result.errors),
        "renderSize": [result.render_size[0], result.render_size[1]],
        "nonBackgroundPixels": result.non_background_pixels,
        "output": str(result.output) if result.output else "",
    }


def export_field_pack(layout: dict[str, Any], layout_path: Path, output: Path) -> dict[str, Any]:
    env_example = default_env_example_path()
    if not env_example.exists():
        return {"ok": False, "errors": [f"Pi HUD env example not found: {env_example}"]}
    assets_dir = default_warning_icon_assets_dir()
    if not assets_dir.exists():
        return {"ok": False, "errors": [f"Pi HUD warning icon assets not found: {assets_dir}"]}
    nav_assets_dir = default_nav_icon_assets_dir()
    if not nav_assets_dir.exists():
        return {"ok": False, "errors": [f"Pi HUD navigation icon assets not found: {nav_assets_dir}"]}

    canvas = layout["canvas"]
    with tempfile.TemporaryDirectory(prefix="headunit-editor-field-pack-") as temp_dir:
        preview_path = Path(temp_dir) / "layout-preview.png"
        verification = verify_layout(
            layout,
            width=canvas["width"],
            height=canvas["height"],
            output=preview_path,
            require_handoff=True,
        )
        if not verification.ok:
            return {"ok": False, "errors": verification.errors}

        layout_name = layout_path.name or DEFAULT_LAYOUT_NAME
        layout_entry_path = f"layouts/{layout_name}"
        layout_bytes = json.dumps(layout, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
        env_bytes = env_example.read_bytes()
        preview_bytes = preview_path.read_bytes()
        vehicle_entries = field_pack_vehicle_entries(layout)
        asset_entries = field_pack_asset_entries(assets_dir, nav_assets_dir)
        manifest = build_field_pack_manifest(
            layout,
            layout_path,
            layout_entry_path,
            layout_bytes,
            env_bytes,
            preview_bytes,
            vehicle_entries,
            asset_entries,
            verification,
        )

        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(layout_entry_path, layout_bytes)
            for archive_path, payload in vehicle_entries:
                archive.writestr(archive_path, payload)
            for archive_path, payload in asset_entries:
                archive.writestr(archive_path, payload)
            archive.writestr("config/pi-hud.env.example", env_bytes)
            archive.writestr("preview/layout-preview.png", preview_bytes)
            archive.writestr("README-pi-field-pack.txt", editor_field_pack_readme(layout_entry_path))
            archive.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n")

    return {
        "ok": True,
        "errors": [],
        "output": str(output),
        "renderSize": [verification.render_size[0], verification.render_size[1]],
        "nonBackgroundPixels": verification.non_background_pixels,
    }


def field_pack_vehicle_entries(layout: dict[str, Any]) -> list[tuple[str, bytes]]:
    profiles = profile_map(load_vehicle_profiles(default_vehicle_profile_paths()), layout)
    entries: list[tuple[str, bytes]] = []
    for vehicle_id, profile in sorted(profiles.items()):
        payload = json.dumps(profile, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
        entries.append((f"vehicles/{vehicle_id}.json", payload))
    return entries


def field_pack_asset_entries(warning_assets_dir: Path, nav_assets_dir: Path) -> list[tuple[str, bytes]]:
    entries: list[tuple[str, bytes]] = []
    for asset_path in sorted(path for path in warning_assets_dir.glob("*.png") if path.is_file()):
        entries.append((f"pi-hud/assets/warning-icons/{asset_path.name}", asset_path.read_bytes()))
    for asset_path in sorted(path for path in nav_assets_dir.glob("*.png") if path.is_file()):
        entries.append((f"pi-hud/assets/nav-icons/{asset_path.name}", asset_path.read_bytes()))
    return entries


def build_field_pack_manifest(
    layout: dict[str, Any],
    layout_path: Path,
    layout_entry_path: str,
    layout_bytes: bytes,
    env_bytes: bytes,
    preview_bytes: bytes,
    vehicle_entries: list[tuple[str, bytes]],
    asset_entries: list[tuple[str, bytes]],
    verification: Any,
) -> dict[str, Any]:
    vehicles = [
        {"path": archive_path, "size": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
        for archive_path, payload in vehicle_entries
    ]
    assets = [
        {"path": archive_path, "size": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
        for archive_path, payload in asset_entries
    ]
    return {
        "kind": "headunit-pi-field-pack",
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "selected_vehicle": layout.get("selected_vehicle", ""),
        "layout": {
            "path": layout_entry_path,
            "source": str(layout_path),
            "size": len(layout_bytes),
            "sha256": hashlib.sha256(layout_bytes).hexdigest(),
            "render_size": [verification.render_size[0], verification.render_size[1]],
            "non_background_pixels": verification.non_background_pixels,
            "require_handoff": True,
        },
        "preview": {
            "path": "preview/layout-preview.png",
            "size": len(preview_bytes),
            "sha256": hashlib.sha256(preview_bytes).hexdigest(),
            "render_size": [verification.render_size[0], verification.render_size[1]],
            "non_background_pixels": verification.non_background_pixels,
        },
        "vehicles": vehicles,
        "assets": assets,
        "env_example": {
            "path": "config/pi-hud.env.example",
            "source": str(default_env_example_path()),
            "size": len(env_bytes),
            "sha256": hashlib.sha256(env_bytes).hexdigest(),
        },
        "install_targets": {
            "app_dir": "/opt/headunit-pi-hud",
            "env_file": "/etc/headunit-pi-hud.env",
            "layout": f"/opt/headunit-pi-hud/{layout_entry_path}",
        },
    }


def editor_field_pack_readme(layout_archive_path: str) -> str:
    return f"""Headunit Pi HUD field pack

Contents:
- {layout_archive_path}
- vehicles/*.json
- pi-hud/assets/warning-icons/*.png
- pi-hud/assets/nav-icons/*.png
- config/pi-hud.env.example
- preview/layout-preview.png
- manifest.json

On the Raspberry Pi after pi-hud/scripts/install-pi.sh has installed the runtime:

  /opt/headunit-pi-hud/.venv/bin/python \\
    /opt/headunit-pi-hud/pi-hud/scripts/apply-field-pack.py \\
    headunit-pi-field-pack.zip

  /opt/headunit-pi-hud/.venv/bin/python \\
    /opt/headunit-pi-hud/pi-hud/scripts/acceptance-check.py --probe-display --probe-inputs --json

  sudo systemctl restart headunit-pi-hud.service

Acceptance output is written to:

  /opt/headunit-pi-hud/vehicle-baseline/acceptance-check.json

If /etc/headunit-pi-hud.env is already edited for the car, merge the new env example manually instead of overwriting it.
"""


if __name__ == "__main__":
    raise SystemExit(main())
