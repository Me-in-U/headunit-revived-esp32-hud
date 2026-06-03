from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class BleCharacteristicInfo:
    uuid: str
    properties: tuple[str, ...]
    service_uuid: str = ""
    description: str = ""


@dataclass(frozen=True)
class BleObdPair:
    rx_uuid: str
    tx_uuid: str


@dataclass(frozen=True)
class BleObdDiscoveryResult:
    rx_candidates: list[BleCharacteristicInfo]
    tx_candidates: list[BleCharacteristicInfo]
    pairs: list[BleObdPair]


def classify_ble_obd_characteristics(characteristics: Iterable[BleCharacteristicInfo]) -> BleObdDiscoveryResult:
    infos = list(characteristics)
    rx_candidates = [info for info in infos if _has_any_property(info, {"notify", "indicate"})]
    tx_candidates = [info for info in infos if _has_any_property(info, {"write", "write-without-response"})]
    pairs: list[BleObdPair] = []
    for rx in rx_candidates:
        for tx in tx_candidates:
            if rx.uuid == tx.uuid and len(rx_candidates) > 1:
                continue
            pairs.append(BleObdPair(rx.uuid, tx.uuid))
    return BleObdDiscoveryResult(rx_candidates=rx_candidates, tx_candidates=tx_candidates, pairs=pairs)


def characteristic_infos_from_services(services: Any) -> list[BleCharacteristicInfo]:
    infos: list[BleCharacteristicInfo] = []
    for service in services:
        service_uuid = str(getattr(service, "uuid", ""))
        for characteristic in getattr(service, "characteristics", []):
            infos.append(
                BleCharacteristicInfo(
                    uuid=str(getattr(characteristic, "uuid", "")),
                    properties=tuple(str(prop).lower() for prop in getattr(characteristic, "properties", [])),
                    service_uuid=service_uuid,
                    description=str(getattr(characteristic, "description", "")),
                )
            )
    return infos


def env_lines_for_ble_obd(mac: str, rx_uuid: str, tx_uuid: str) -> list[str]:
    return [
        "HEADUNIT_HUD_OBD_PORT=",
        f"HEADUNIT_HUD_OBD_BLE_MAC={mac}",
        f"HEADUNIT_HUD_OBD_BLE_RX_UUID={rx_uuid}",
        f"HEADUNIT_HUD_OBD_BLE_TX_UUID={tx_uuid}",
    ]


def _has_any_property(info: BleCharacteristicInfo, names: set[str]) -> bool:
    properties = {prop.lower() for prop in info.properties}
    return bool(properties & names)
