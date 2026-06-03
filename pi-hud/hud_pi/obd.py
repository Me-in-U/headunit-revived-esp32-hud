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
    bytes_ = payload_bytes_after(response, positive_service)
    dtcs: list[str] = []
    for index in range(0, len(bytes_) - 1, 2):
        decoded = decode_dtc_pair(bytes_[index], bytes_[index + 1])
        if decoded is None:
            break
        dtcs.append(decoded)
    return dtcs
