"""Build Spring delivery payloads from validated silver records."""
from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Dict, Sequence

from app.pipelines.models import DeliveryPayload, GoldBrandPayload, SilverRecord

BRAND_LABELS: Dict[str, str] = {
    "Starbucks": "스타벅스",
    "MegaCoffee": "메가커피",
}


def _product_id(record: SilverRecord) -> str:
    basis = f"{record.brand}:{record.product_name}:{record.size}"
    digest = hashlib.sha1(basis.encode("utf-8")).hexdigest()
    return f"{record.brand[:2].upper()}-{digest[:10]}"


def build_spring_payload(records: Sequence[SilverRecord]) -> DeliveryPayload:
    brand_items: Dict[str, list[dict]] = {}
    for record in records:
        entry = {
            "productId": _product_id(record),
            "brand": record.brand,
            "productName": record.product_name,
            "size": record.size,
            "beverageType": record.beverage_type,
            "isLiked": False,
            "sourceBatch": record.source_batch,
            "validationStatus": record.validation_status,
            "notes": record.notes,
            "nutrition": record.nutrition.model_dump(mode="json"),
        }
        brand_items.setdefault(record.brand, []).append(entry)

    brands_payload = [
        GoldBrandPayload(
            korean_brand_name=BRAND_LABELS.get(brand, brand),
            items=items,
        )
        for brand, items in brand_items.items()
    ]
    return DeliveryPayload(brands=brands_payload, generated_at=datetime.utcnow())
