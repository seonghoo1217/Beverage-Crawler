"""Starbucks crawler with schema drift detection and Bronze-ready payloads."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

import requests

from app.config.settings import settings
from app.observability.logging import log_event
from app.pipelines.models import BronzeRecord, SourceArtifact
from app.pipelines.validators.dedup_validator import calculate_checksum


@dataclass
class StarbucksMenuItem:
    product_name: str
    beverage_type: str
    image_url: str
    nutrition_raw: dict


class StarbucksCrawler:
    CATEGORY_MAP = {
        "W0000003": "ESPRESSO",
        "W0000171": "COLD_BREW",
        "W0000060": "COLD_BREW",
        "W0000004": "FRAPPUCCINO",
        "W0000005": "BLENDED",
        "W0000075": "TEA",
        "W0000422": "REFRESHER",
        "W0000061": "FIZZIO",
        "W0000053": "OTHERS",
        "W0000062": "JUICE_YOGURT",
    }
    EXPECTED_FIELDS = {
        "product_NM",
        "kcal",
        "sat_FAT",
        "protein",
        "sodium",
        "sugars",
        "caffeine",
        "file_PATH",
    }

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (compatible; StarbucksBot/1.0)",
                "Accept": "application/json",
            }
        )

    def fetch_all(self) -> list[StarbucksMenuItem]:
        payloads: list[StarbucksMenuItem] = []
        for code, beverage_type in self.CATEGORY_MAP.items():
            url = f"https://www.starbucks.co.kr/upload/json/menu/{code}.js"
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                log_event(
                    "starbucks.crawl_http_error",
                    url=url,
                    status=response.status_code,
                )
                continue
            text = response.text.replace("\ufeff", "")
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                log_event("starbucks.schema_drift", url=url, reason="json_decode_failed")
                continue
            for entry in data.get("list", []):
                missing = self.EXPECTED_FIELDS - entry.keys()
                if missing:
                    log_event(
                        "starbucks.schema_drift",
                        url=url,
                        missing_fields=",".join(sorted(missing)),
                    )
                    continue
                payloads.append(
                    StarbucksMenuItem(
                        product_name=entry["product_NM"].strip(),
                        beverage_type=beverage_type,
                        image_url=f"https://www.starbucks.co.kr{entry['file_PATH']}",
                        nutrition_raw={
                            "servingKcal": entry["kcal"],
                            "saturatedFatG": entry["sat_FAT"],
                            "proteinG": entry["protein"],
                            "sodiumMg": entry["sodium"],
                            "sugarG": entry["sugars"],
                            "caffeineMg": entry["caffeine"],
                        },
                    )
                )
            time.sleep(0.2)
        return payloads


def _normalize_int(value: str | int | float | None) -> int:
    if value in (None, "", " "):
        return 0
    try:
        return int(float(str(value).replace(",", "")))
    except ValueError:
        return 0


def to_bronze_records(
    items: Iterable[StarbucksMenuItem],
    batch_id: str,
    ocr_lookup: dict[tuple[str, str], dict] | None = None,
) -> List[BronzeRecord]:
    ocr_lookup = ocr_lookup or {}
    records: list[BronzeRecord] = []
    for item in items:
        key = (item.product_name.upper(), "TALL")
        ocr_payload = ocr_lookup.get(key)
        source = SourceArtifact(
            brand="Starbucks",
            batch_id=batch_id,
            source_type="HTML",
            uri="https://www.starbucks.co.kr/menu/drink_list.do",
            checksum=calculate_checksum(item.nutrition_raw),
            collected_at=datetime.utcnow(),
        )
        records.append(
            BronzeRecord(
                brand="Starbucks",
                product_name=item.product_name,
                size="TALL",
                beverage_type=item.beverage_type,
                nutrition_raw={
                    "servingMl": 0,
                    **{k: _normalize_int(v) for k, v in item.nutrition_raw.items()},
                },
                source=source,
                ocr_nutrition=ocr_payload.get("nutrition") if ocr_payload else None,
                ocr_confidence=ocr_payload.get("confidence") if ocr_payload else None,
            )
        )
    return records


def get_crawled_data() -> list[dict]:
    """Backward-compatible helper returning dict payloads for existing callers."""
    crawler = StarbucksCrawler()
    items = crawler.fetch_all()
    return [
        {
            "brand": "STARBUCKS",
            "name": item.product_name,
            "image": item.image_url,
            "beverageType": item.beverage_type,
            "beverageNutritions": {"TALL": item.nutrition_raw},
        }
        for item in items
    ]
