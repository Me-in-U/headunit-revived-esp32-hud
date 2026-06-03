from __future__ import annotations

from dataclasses import dataclass


FIELD_PACK_KIND = "headunit-pi-field-pack"
FIELD_PACK_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class PayloadEntry:
    path: str
    payload: bytes
    source: str = ""
