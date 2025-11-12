"""Convert Bronze records into Silver tier payloads and track diffs."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

from app.pipelines.models import BronzeRecord, NutritionProfile, SilverRecord
from app.pipelines.validators.starbucks_validator import (
    StarbucksValidationSummary,
    evaluate_record,
)
from app.storage.silver.snapshot import load_latest_snapshot, persist_snapshot


@dataclass
class SilverDiff:
    new_items: list[str]
    removed_items: list[str]
    changed_items: list[str]


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
                notes=", ".join(validation.offending_fields)
                if validation.offending_fields
                else None,
            )
        )
    return silver_records, summary


def persist_silver_records(
    brand: str, batch_id: str, records: Sequence[SilverRecord]
) -> Path:
    return persist_snapshot(brand=brand, batch_id=batch_id, records=records)


def generate_diff(
    previous_snapshot: dict | None, current_records: Sequence[SilverRecord]
) -> SilverDiff | None:
    if not previous_snapshot:
        return None
    prev_map = {rec["product_name"]: rec for rec in previous_snapshot.get("records", [])}
    current_map = {rec.product_name: rec for rec in current_records}

    new_items = [name for name in current_map.keys() if name not in prev_map]
    removed_items = [name for name in prev_map.keys() if name not in current_map]
    changed_items: list[str] = []
    for name in current_map.keys() & prev_map.keys():
        current_dump = json.dumps(
            current_map[name].model_dump(mode="json"), sort_keys=True
        )
        previous_dump = json.dumps(prev_map[name], sort_keys=True)
        if current_dump != previous_dump:
            changed_items.append(name)
    return SilverDiff(new_items=new_items, removed_items=removed_items, changed_items=changed_items)


def write_change_log(diff: SilverDiff | None, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not diff:
        content = "# MegaCoffee Change Log\n\n첫 스냅샷입니다. 비교 대상이 없습니다.\n"
        path.write_text(content, encoding="utf-8")
        return
    content = f"""# MegaCoffee Change Log

- New items: {diff.new_items or ['없음']}
- Removed items: {diff.removed_items or ['없음']}
- Changed items: {diff.changed_items or ['없음']}
"""
    path.write_text(content, encoding="utf-8")
