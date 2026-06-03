from __future__ import annotations

from typing import Any


DEFAULT_LANGUAGE = "en"

WARNING_LABELS = {
    "en": {
        "warnings.door_open": "DOOR",
        "warnings.battery": "BATT",
        "warnings.brake": "BRAKE",
        "warnings.abs": "ABS",
        "warnings.airbag": "AIR",
        "warnings.oil_pressure": "OIL",
        "warnings.check_engine": "ENG",
        "warnings.eps": "EPS",
        "warnings.coolant_temp": "TEMP",
        "warnings.seatbelt": "BELT",
        "warnings.low_fuel": "FUEL",
        "warnings.tire_pressure": "TIRE",
        "warnings.high_beam": "HIGH",
        "warnings.low_beam": "LOW",
        "warnings.parking_lights": "PARK",
        "warnings.fog_light": "FOG",
        "warnings.washer_fluid": "WASH",
        "warnings.cruise_control": "CRUISE",
        "warnings.traction_control": "TRAC",
        "warnings.glow_plug": "GLOW",
    },
    "ko": {
        "warnings.door_open": "도어",
        "warnings.battery": "배터리",
        "warnings.brake": "브레이크",
        "warnings.abs": "ABS",
        "warnings.airbag": "에어백",
        "warnings.oil_pressure": "오일",
        "warnings.check_engine": "엔진",
        "warnings.eps": "EPS",
        "warnings.coolant_temp": "수온",
        "warnings.seatbelt": "벨트",
        "warnings.low_fuel": "연료",
        "warnings.tire_pressure": "타이어",
        "warnings.high_beam": "상향",
        "warnings.low_beam": "하향",
        "warnings.parking_lights": "미등",
        "warnings.fog_light": "안개등",
        "warnings.washer_fluid": "워셔액",
        "warnings.cruise_control": "크루즈",
        "warnings.traction_control": "구동",
        "warnings.glow_plug": "예열",
    },
}

WARNING_ACTIVE_COLORS = {
    "warnings.door_open": "#ee2024",
    "warnings.battery": "#ee2024",
    "warnings.brake": "#ee2024",
    "warnings.abs": "#ffae00",
    "warnings.airbag": "#ee2024",
    "warnings.oil_pressure": "#ee2024",
    "warnings.check_engine": "#ffae00",
    "warnings.eps": "#ee2024",
    "warnings.coolant_temp": "#ee2024",
    "warnings.seatbelt": "#ee2024",
    "warnings.low_fuel": "#ffae00",
    "warnings.tire_pressure": "#ffae00",
    "warnings.high_beam": "#40a7ff",
    "warnings.low_beam": "#24d36b",
    "warnings.parking_lights": "#24d36b",
    "warnings.fog_light": "#24d36b",
    "warnings.washer_fluid": "#ffae00",
    "warnings.cruise_control": "#24d36b",
    "warnings.traction_control": "#ffae00",
    "warnings.glow_plug": "#ffae00",
}


def normalize_language(language: Any, fallback: str = DEFAULT_LANGUAGE) -> str:
    value = str(language or fallback).strip().lower()
    if value.startswith("ko"):
        return "ko"
    if value.startswith("en"):
        return "en"
    return fallback if fallback in {"ko", "en"} else DEFAULT_LANGUAGE


def format_value(raw_value: Any, language: str = DEFAULT_LANGUAGE) -> str:
    language = normalize_language(language)
    if isinstance(raw_value, bool):
        if language == "ko":
            return "켜짐" if raw_value else "꺼짐"
        return "ON" if raw_value else "OFF"
    if isinstance(raw_value, list):
        if language == "ko":
            return ", ".join(str(item) for item in raw_value) if raw_value else "없음"
        return ", ".join(str(item) for item in raw_value) if raw_value else "NONE"
    return str(raw_value)


def warning_label(binding: str, language: str) -> str:
    language = normalize_language(language)
    fallback = binding.split(".")[-1].upper()
    return WARNING_LABELS.get(language, WARNING_LABELS[DEFAULT_LANGUAGE]).get(binding, fallback)


def warning_active_color(binding: str, default: str = "#ff3b30") -> str:
    return WARNING_ACTIVE_COLORS.get(binding, default)
