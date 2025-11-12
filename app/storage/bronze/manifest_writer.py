"""Persist Bronze tier manifests for each brand/batch."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from app.config.settings import settings
from app.pipelines.models import BronzeRecord


def write_manifest(brand: str, batch_id: str, records: Sequence[BronzeRecord]) -> Path:
    target_dir = settings.storage_root / "bronze" / brand.lower() / batch_id
    target_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "batchId": batch_id,
        "brand": brand,
        "recordCount": len(records),
        "records": [record.model_dump(mode="json") for record in records],
    }
    manifest_path = target_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    return manifest_path
