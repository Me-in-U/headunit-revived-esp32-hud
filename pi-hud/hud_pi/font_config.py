from __future__ import annotations

from dataclasses import dataclass

from hud_pi.display_format import normalize_language


CJK_FONT_CANDIDATES = (
    "Noto Sans CJK KR",
    "Noto Sans KR",
    "NanumGothic",
    "Malgun Gothic",
    "Apple SD Gothic Neo",
    "Arial Unicode MS",
)


@dataclass(frozen=True)
class FontRequest:
    backend: str
    family: str | None


def font_request(family: str | None, language: str | None) -> FontRequest:
    normalized_family = str(family or "default").strip() or "default"
    normalized_language = normalize_language(language or "en")
    if normalized_family.lower() != "default":
        return FontRequest("system", normalized_family)
    if normalized_language == "ko":
        return FontRequest("system", ", ".join(CJK_FONT_CANDIDATES))
    return FontRequest("builtin", None)
