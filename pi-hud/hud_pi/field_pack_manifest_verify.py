from __future__ import annotations

import hashlib
import json
import zipfile
from typing import Any

from hud_pi.field_pack_manifest_model import FIELD_PACK_KIND, FIELD_PACK_SCHEMA_VERSION
from hud_pi.field_pack_manifest_paths import validate_archive_path


def load_manifest(archive: zipfile.ZipFile) -> dict[str, Any]:
    try:
        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
    except KeyError as error:
        raise ValueError("manifest.json is missing") from error
    except json.JSONDecodeError as error:
        raise ValueError("manifest.json is not valid JSON") from error
    if not isinstance(manifest, dict):
        raise ValueError("manifest.json must be an object")
    if manifest.get("kind") != FIELD_PACK_KIND:
        raise ValueError(f"manifest kind is not {FIELD_PACK_KIND}")
    if manifest.get("schema_version") != FIELD_PACK_SCHEMA_VERSION:
        raise ValueError(f"manifest schema_version must be {FIELD_PACK_SCHEMA_VERSION}")
    return manifest


def manifest_entries(manifest: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    layout = require_entry(manifest.get("layout"), "layout")
    vehicles = manifest.get("vehicles", [])
    if not isinstance(vehicles, list):
        raise ValueError("manifest vehicles must be a list")
    vehicle_entries = [require_entry(vehicle, f"vehicles[{index}]") for index, vehicle in enumerate(vehicles)]
    assets = manifest.get("assets", [])
    if not isinstance(assets, list):
        raise ValueError("manifest assets must be a list")
    asset_entries = [require_entry(asset, f"assets[{index}]") for index, asset in enumerate(assets)]
    env_example = require_entry(manifest.get("env_example"), "env_example")
    return layout, vehicle_entries, asset_entries, env_example


def require_entry(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"manifest {label} must be an object")
    path = value.get("path")
    digest = value.get("sha256")
    if not isinstance(path, str) or not path.strip():
        raise ValueError(f"manifest {label}.path is missing")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError(f"manifest {label}.sha256 is missing")
    validate_archive_path(path)
    return value


def verify_payloads(archive: zipfile.ZipFile, entries: list[dict[str, Any]]) -> dict[str, bytes]:
    payloads: dict[str, bytes] = {}
    for entry in entries:
        archive_path = entry["path"]
        try:
            payload = archive.read(archive_path)
        except KeyError as error:
            raise ValueError(f"package file is missing: {archive_path}") from error
        digest = hashlib.sha256(payload).hexdigest()
        if digest.lower() != str(entry["sha256"]).lower():
            raise ValueError(f"sha256 mismatch for {archive_path}")
        payloads[archive_path] = payload
    return payloads
