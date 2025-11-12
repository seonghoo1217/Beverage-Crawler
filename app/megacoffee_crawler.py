"""MegaCoffee crawler limited to menu_category1=1&menu_category2=1."""
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List

import requests
from bs4 import BeautifulSoup

from app.config.settings import settings
from app.observability.logging import log_event
from app.pipelines.models import BronzeRecord, SourceArtifact
from app.pipelines.validators.dedup_validator import calculate_checksum
from app.pipelines.mappers.megacoffee_mapper import resolve_beverage_type


@dataclass
class MegaCoffeeMenuItem:
    product_name: str
    beverage_type: str | None
    image_url: str
    nutrition_raw: dict


class MegaCoffeeCrawler:
    BASE_URL = "https://www.mega-mgccoffee.com"
    MENU_URL = f"{BASE_URL}/menu/menu.php"
    CATEGORY1 = "1"
    CATEGORY2 = "1"

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (compatible; MegaCoffeeBot/1.0)",
                "Referer": f"{self.BASE_URL}/menu/menu_list.html",
            }
        )

    def fetch_all(self) -> list[MegaCoffeeMenuItem]:
        page = 1
        items: list[MegaCoffeeMenuItem] = []
        while True:
            params = {
                "menu_category1": self.CATEGORY1,
                "menu_category2": self.CATEGORY2,
                "list_checkbox_all": "all",
                "page": page,
            }
            response = self.session.get(self.MENU_URL, params=params, timeout=15)
            if response.status_code != 200:
                raise RuntimeError(
                    f"MegaCoffee category fetch failed {response.status_code}"
                )
            soup = BeautifulSoup(response.text, "lxml")
            li_nodes = soup.find_all("li")
            if not li_nodes:
                break
            for node in li_nodes:
                parsed = self._parse_node(node)
                if parsed:
                    items.append(parsed)
            page += 1
            time.sleep(0.2)
        if not items:
            raise RuntimeError("MegaCoffee crawl returned zero beverages")
        return items

    def _parse_node(self, node) -> MegaCoffeeMenuItem | None:
        name_tag = node.select_one(".cont_text_title b")
        if not name_tag:
            return None
        raw_name = name_tag.get_text(strip=True)
        cleaned_name = (
            raw_name.replace("(HOT)", "").replace("(ICE)", "").replace("(ICED)", "").strip()
        )
        img_tag = node.select_one(".cont_gallery_list_img img")
        if not img_tag:
            return None
        img_url = img_tag.get("src", "")
        modal = node.select_one(".inner_modal")
        if not modal:
            return None
        modal_text = modal.get_text(separator=" ")
        nutrition_raw = self._extract_nutrition(modal_text)
        beverage_type = resolve_beverage_type(cleaned_name, modal.get("data-type"))
        return MegaCoffeeMenuItem(
            product_name=cleaned_name,
            beverage_type=beverage_type,
            image_url=img_url,
            nutrition_raw=nutrition_raw,
        )

    @staticmethod
    def _extract_nutrition(text: str) -> dict:
        def _match(pattern: str) -> float:
            match = re.search(pattern, text)
            return float(match.group(1)) if match else 0.0

        return {
            "servingMl": _match(r"([0-9.]+)\s*ml"),
            "servingKcal": _match(r"1회 제공량\s*([0-9.]+)\s*kcal"),
            "sugarG": _match(r"당류\s*([0-9.]+)\s*g"),
            "proteinG": _match(r"단백질\s*([0-9.]+)\s*g"),
            "saturatedFatG": _match(r"포화지방\s*([0-9.]+)\s*g"),
            "sodiumMg": _match(r"나트륨\s*([0-9.]+)\s*mg"),
            "caffeineMg": _match(r"카페인\s*([0-9.]+)\s*mg"),
        }


def to_bronze_records(
    items: Iterable[MegaCoffeeMenuItem], batch_id: str
) -> List[BronzeRecord]:
    records: list[BronzeRecord] = []
    for item in items:
        source = SourceArtifact(
            brand="MegaCoffee",
            batch_id=batch_id,
            source_type="HTML",
            uri=f"{MegaCoffeeCrawler.BASE_URL}/menu/?menu_category1=1&menu_category2=1",
            checksum=calculate_checksum(item.nutrition_raw),
            collected_at=datetime.utcnow(),
        )
        records.append(
            BronzeRecord(
                brand="MegaCoffee",
                product_name=item.product_name,
                size="MEGA",
                beverage_type=item.beverage_type,
                nutrition_raw=item.nutrition_raw,
                source=source,
            )
        )
    return records


def get_megacoffee_data() -> list[dict]:
    crawler = MegaCoffeeCrawler()
    items = crawler.fetch_all()
    return [
        {
            "brand": "MEGA_COFFEE",
            "name": item.product_name,
            "image": item.image_url,
            "beverageType": item.beverage_type,
            "beverageNutritions": [{"size": "MEGA", **item.nutrition_raw}],
        }
        for item in items
    ]
