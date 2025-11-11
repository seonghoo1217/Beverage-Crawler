"""Pydantic models shared across Bronze → Silver → Gold tiers."""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Sequence

from pydantic import BaseModel, Field, HttpUrl

BrandName = Literal["Starbucks", "MegaCoffee"]
SizeCode = Literal["TALL", "GRANDE", "VENTI", "MEGA"]


class SourceArtifact(BaseModel):
    brand: BrandName
    batch_id: str
    source_type: Literal["HTML", "PNG"]
    uri: HttpUrl | str
    checksum: str
    collected_at: datetime


class NutritionProfile(BaseModel):
    serving_ml: int = Field(ge=0)
    serving_kcal: int = Field(ge=0)
    saturated_fat_g: float = Field(ge=0)
    protein_g: float = Field(ge=0)
    sodium_mg: float = Field(ge=0)
    sugar_g: float = Field(ge=0)
    caffeine_mg: float = Field(ge=0)


class BronzeRecord(BaseModel):
    brand: BrandName
    product_name: str
    size: SizeCode
    beverage_type: str | None
    nutrition_raw: dict
    source: SourceArtifact
    ocr_confidence: float | None = Field(default=None, ge=0, le=1)


class SilverRecord(BaseModel):
    brand: BrandName
    product_name: str
    size: SizeCode
    beverage_type: str
    nutrition: NutritionProfile
    source_batch: str
    validation_status: Literal["clean", "needs_review"]
    notes: str | None = None


class GoldBrandPayload(BaseModel):
    korean_brand_name: str
    items: Sequence[dict]


class DeliveryPayload(BaseModel):
    brands: Sequence[GoldBrandPayload]
    generated_at: datetime


def bronze_schema() -> dict:
    """Expose JSON schema for bronze tier validations."""
    return BronzeRecord.model_json_schema()


def silver_schema() -> dict:
    return SilverRecord.model_json_schema()


def gold_schema() -> dict:
    return DeliveryPayload.model_json_schema()
