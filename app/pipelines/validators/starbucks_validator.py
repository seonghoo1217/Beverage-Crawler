"""Validation logic for Starbucks nutrition data."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.pipelines.models import BronzeRecord

THRESHOLD = 0.02  # 2% difference
FIELDS = [
    ("servingKcal", "servingKcal"),
    ("saturatedFatG", "saturatedFatG"),
    ("proteinG", "proteinG"),
    ("sodiumMg", "sodiumMg"),
    ("sugarG", "sugarG"),
    ("caffeineMg", "caffeineMg"),
]


@dataclass
class ValidationResult:
    product_name: str
    status: str
    offending_fields: list[str] = field(default_factory=list)


@dataclass
class StarbucksValidationSummary:
    inspected: int = 0
    clean: int = 0
    needs_review: int = 0
    offenders: list[str] = field(default_factory=list)

    def track(self, result: ValidationResult) -> None:
        self.inspected += 1
        if result.status == "clean":
            self.clean += 1
        else:
            self.needs_review += 1
            self.offenders.append(result.product_name)


def evaluate_record(record: BronzeRecord) -> ValidationResult:
    if not record.ocr_nutrition:
        return ValidationResult(product_name=record.product_name, status="clean")
    offending: list[str] = []
    for target_key, ocr_key in FIELDS:
        official = float(record.nutrition_raw.get(target_key, 0))
        ocr_value = float(record.ocr_nutrition.get(ocr_key, 0))
        baseline = max(official, 1.0)
        delta = abs(official - ocr_value) / baseline
        if delta > THRESHOLD:
            offending.append(target_key)
    status = "needs_review" if offending else "clean"
    return ValidationResult(
        product_name=record.product_name, status=status, offending_fields=offending
    )
