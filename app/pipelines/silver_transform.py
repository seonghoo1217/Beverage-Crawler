"""Convert Bronze Starbucks records into Silver tier payloads."""
from __future__ import annotations

from typing import Iterable, List

from app.pipelines.models import BronzeRecord, NutritionProfile, SilverRecord
from app.pipelines.validators.starbucks_validator import (
    StarbucksValidationSummary,
    evaluate_record,
)


def _nutrition_from_raw(raw: dict) -> NutritionProfile:
    return NutritionProfile(
        serving_ml=int(raw.get("servingMl", 0)),
        serving_kcal=int(raw.get("servingKcal", 0)),
        saturated_fat_g=float(raw.get("saturatedFatG", 0)),
        protein_g=float(raw.get("proteinG", 0)),
        sodium_mg=float(raw.get("sodiumMg", 0)),
        sugar_g=float(raw.get("sugarG", 0)),
        caffeine_mg=float(raw.get("caffeineMg", 0)),
    )


def convert_to_silver(
    records: Iterable[BronzeRecord],
) -> tuple[list[SilverRecord], StarbucksValidationSummary]:
    silver_records: list[SilverRecord] = []
    summary = StarbucksValidationSummary()
    for record in records:
        validation = evaluate_record(record)
        summary.track(validation)
        silver_records.append(
            SilverRecord(
                brand=record.brand,
                product_name=record.product_name,
                size=record.size,
                beverage_type=record.beverage_type or "UNKNOWN",
                nutrition=_nutrition_from_raw(record.nutrition_raw),
                source_batch=record.source.batch_id,
                validation_status=validation.status,
                notes=", ".join(validation.offending_fields) if validation.offending_fields else None,
            )
        )
    return silver_records, summary
