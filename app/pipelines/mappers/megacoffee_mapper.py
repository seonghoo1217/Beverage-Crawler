"""Infer MegaCoffee beverage types when source data is missing."""
from __future__ import annotations

KEYWORDS = [
    ("COFFEE", ["커피", "아메리카노", "라떼", "에스프레소"]),
    ("SMOOTHIE_FRAPPE", ["스무디", "프라페", "쉐이크"]),
    ("ADE_JUICE", ["에이드", "주스"]),
    ("TEA", ["티", "차", "녹차"]),
    ("CHOCOLATE", ["초코", "핫초코"]),
    ("COLD_BREW", ["콜드 브루"]),
    ("BLENDED", ["블렌디드"]),
    ("FIZZIO", ["피지오"]),
    ("REFRESHER", ["리프레셔"]),
]


def resolve_beverage_type(name: str, provided: str | None) -> str:
    provided = (provided or "").strip()
    if provided:
        return provided.upper()
    lowered = name.lower()
    for target, keywords in KEYWORDS:
        if any(keyword.lower() in lowered for keyword in keywords):
            return target
    return "OTHERS"
