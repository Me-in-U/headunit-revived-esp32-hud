from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Iterable


def load_vehicle_profile_entries(paths: Iterable[str | Path]) -> list[tuple[Path, dict[str, Any]]]:
    profiles_by_id: dict[str, tuple[Path, dict[str, Any]]] = {}
    for profile_path in _profile_files(paths):
        with profile_path.open("r", encoding="utf-8") as handle:
            profile = json.load(handle)
        _validate_profile(profile, profile_path)
        profiles_by_id[str(profile["id"])] = (profile_path, profile)
    return [profiles_by_id[key] for key in sorted(profiles_by_id)]


def load_vehicle_profiles(paths: Iterable[str | Path]) -> list[dict[str, Any]]:
    return [profile for _, profile in load_vehicle_profile_entries(paths)]


def upsert_vehicle_profile(layout: dict[str, Any], profile: dict[str, Any], select: bool = False) -> None:
    _validate_profile(profile, Path("<memory>"))
    vehicles = layout.setdefault("vehicles", [])
    profile_copy = copy.deepcopy(profile)
    for index, vehicle in enumerate(vehicles):
        if isinstance(vehicle, dict) and vehicle.get("id") == profile_copy["id"]:
            vehicles[index] = profile_copy
            break
    else:
        vehicles.append(profile_copy)
    if select:
        layout["selected_vehicle"] = profile_copy["id"]


def profile_map(profiles: Iterable[dict[str, Any]], layout: dict[str, Any]) -> dict[str, dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for vehicle in layout.get("vehicles", []):
        if isinstance(vehicle, dict) and vehicle.get("id"):
            merged[str(vehicle["id"])] = vehicle
    for profile in profiles:
        if profile.get("id"):
            merged[str(profile["id"])] = profile
    return merged


def _profile_files(paths: Iterable[str | Path]) -> list[Path]:
    files: list[Path] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_dir():
            files.extend(sorted(path.glob("*.json")))
        elif path.is_file():
            files.append(path)
    return files


def _validate_profile(profile: Any, source: Path) -> None:
    if not isinstance(profile, dict):
        raise ValueError(f"{source} must contain a JSON object")
    if not str(profile.get("id", "")).strip():
        raise ValueError(f"{source} vehicle profile is missing id")
    if not str(profile.get("label", "")).strip():
        raise ValueError(f"{source} vehicle profile is missing label")
    profile.setdefault("confirmed", {})
