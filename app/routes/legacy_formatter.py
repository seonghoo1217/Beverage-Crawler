"""Helper to convert Gold payloads into legacy /api/v1/beverages format."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable

LEGACY_BRAND_NAMES = {
    "Starbucks": "STARBUCKS",
    "MegaCoffee": "MEGA_COFFEE",
}


def gold_to_legacy(payload: dict, brand_filter: str | None = None) -> list[dict]:
    """Map the Gold payload into the historical API response format."""
    brand_filter = (brand_filter or "").lower() or None
    grouped: Dict[tuple[str, str], dict] = {}

    for brand_entry in payload.get("brands", []):
        for item in brand_entry.get("items", []):
            brand = item.get("brand")
            if not brand:
                continue
            if brand_filter and brand.lower() != brand_filter:
                continue
            key = (brand, item.get("productName", ""))
            if key not in grouped:
                grouped[key] = {
                    "brand": LEGACY_BRAND_NAMES.get(brand, brand.upper()),
                    "name": item.get("productName"),
                    "image": "",
                    "beverageType": item.get("beverageType"),
                    "beverageNutritions": {} if brand == "Starbucks" else [],
                }
            nutrition = item.get("nutrition", {})
            size = item.get("size")
            if brand == "Starbucks":
                if size:
                    grouped[key]["beverageNutritions"][size] = nutrition
            else:
                entry = {"size": size} if size else {}
                entry.update(nutrition)
                grouped[key]["beverageNutritions"].append(entry)
    return list(grouped.values())
