import unittest

from app.pipelines.merger import merge_brand_records
from app.pipelines.validators.integrity_validator import filter_valid_records
from app.pipelines.models import SilverRecord, NutritionProfile


def _nutrition() -> NutritionProfile:
    return NutritionProfile(
        serving_ml=100,
        serving_kcal=10,
        saturated_fat_g=0.1,
        protein_g=0.2,
        sodium_mg=1,
        sugar_g=2,
        caffeine_mg=5,
    )


def _record(brand: str, name: str, size: str, beverage_type: str = "COFFEE") -> SilverRecord:
    return SilverRecord(
        brand=brand,
        product_name=name,
        size=size,
        beverage_type=beverage_type,
        nutrition=_nutrition(),
        source_batch="batch",
        validation_status="clean",
        notes=None,
    )


class MergeIntegrityTest(unittest.TestCase):
    def test_merge_drops_duplicates(self) -> None:
        records = {
            "Starbucks": [_record("Starbucks", "Latte", "TALL")],
            "MegaCoffee": [_record("MegaCoffee", "Latte", "TALL")],
        }
        result = merge_brand_records(records)
        self.assertEqual(len(result.records), 1)
        self.assertEqual(len(result.conflicts), 1)

    def test_integrity_filters_invalid_size_and_type(self) -> None:
        valid = _record("Starbucks", "Mocha", "GRANDE")
        invalid_size = _record("Starbucks", "ShortDrink", "MEGA")
        missing_type = _record("MegaCoffee", "Americano", "MEGA", beverage_type="")
        cleaned, report = filter_valid_records([valid, invalid_size, missing_type])
        self.assertEqual(len(cleaned), 1)
        self.assertEqual(report.passed, 1)
        self.assertEqual(len(report.blocked), 2)


if __name__ == "__main__":
    unittest.main()
