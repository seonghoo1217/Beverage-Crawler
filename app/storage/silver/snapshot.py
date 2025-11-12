"""Persist and load silver-tier snapshots for diffing."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional

from app.config.settings import settings
from app.pipelines.models import SilverRecord


def _silver_dir(brand: str) -> Path:
    return settings.storage_root / "silver" / brand.lower()


def persist_snapshot(brand: str, batch_id: str, records: Iterable[SilverRecord]) -> Path:
    directory = _silver_dir(brand)
    directory.mkdir(parents=True, exist_ok=True)
    payload = {
        "brand": brand,
        "batchId": batch_id,
        "records": [record.model_dump(mode="json") for record in records],
    }
    snapshot_path = directory / f"{batch_id}.json"
    snapshot_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    latest_path = directory / "latest.json"
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    return snapshot_path


def load_latest_snapshot(brand: str) -> Optional[dict]:
    latest_path = _silver_dir(brand) / "latest.json"
    if not latest_path.exists():
        return None
    return json.loads(latest_path.read_text())
