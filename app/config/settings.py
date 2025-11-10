"""Centralized settings for crawling/OCR batch jobs.
Automatically loaded by FastAPI entrypoints and batch scripts."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict


@dataclass(frozen=True)
class BrandConfig:
    name: str
    crawl_url: str
    schedule_cron: str
    size_whitelist: tuple[str, ...]


@dataclass(frozen=True)
class Settings:
    starbucks: BrandConfig = BrandConfig(
        name="Starbucks",
        crawl_url="https://www.starbucks.co.kr/menu/drink_list.do",
        schedule_cron="0 3 * * *",  # 매일 03:00 KST
        size_whitelist=("TALL", "GRANDE", "VENTI"),
    )
    megacoffee: BrandConfig = BrandConfig(
        name="MegaCoffee",
        crawl_url=(
            "https://www.mega-mgccoffee.com/menu/?menu_category1=1&menu_category2=1"
        ),
        schedule_cron="0 4 * * *",
        size_whitelist=("MEGA",),
    )
    storage_root: Path = Path("app/storage")
    ocr_retry_count: int = 3
    alert_webhook_url: str = ""  # TODO: 채널 확정 시 입력
    additional_brands: Dict[str, BrandConfig] = field(default_factory=dict)


settings = Settings()
