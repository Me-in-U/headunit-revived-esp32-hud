from __future__ import annotations


SYSTEM_PREFIXES = ("P", "C", "B", "U")


def compact_hex(response: str) -> str:
    return "".join(ch for ch in response.upper() if ch in "0123456789ABCDEF")


def payload_bytes_after(response: str, positive_service: str) -> list[int]:
    compact = compact_hex(response)
    index = compact.find(positive_service.upper())
    if index < 0:
        return []
    payload = compact[index + len(positive_service) :]
    return [int(payload[i : i + 2], 16) for i in range(0, len(payload) - 1, 2)]


def decode_dtc_pair(first: int, second: int) -> str | None:
    if first == 0 and second == 0:
        return None
    system = SYSTEM_PREFIXES[(first & 0xC0) >> 6]
    digit_1 = (first & 0x30) >> 4
    digit_2 = first & 0x0F
    return f"{system}{digit_1:X}{digit_2:X}{second:02X}"


def parse_dtc_response(response: str, positive_service: str) -> list[str]:
    dtcs: list[str] = []
    for bytes_ in payload_segments_after(response, positive_service):
        for index in range(0, len(bytes_) - 1, 2):
            decoded = decode_dtc_pair(bytes_[index], bytes_[index + 1])
            if decoded is None:
                break
            dtcs.append(decoded)
    return dtcs


def payload_segments_after(response: str, positive_service: str) -> list[list[int]]:
    compact = compact_hex(response)
    marker = positive_service.upper()
    segments: list[list[int]] = []
    start = 0
    while marker:
        index = compact.find(marker, start)
        if index < 0:
            break
        payload_start = index + len(marker)
        next_index = compact.find(marker, payload_start)
        payload = compact[payload_start : next_index if next_index >= 0 else len(compact)]
        if len(payload) >= 2:
            segments.append([int(payload[i : i + 2], 16) for i in range(0, len(payload) - 1, 2)])
        start = payload_start + max(2, len(payload))
    return segments
