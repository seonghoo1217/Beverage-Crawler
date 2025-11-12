"""Bronze tier ingestion routines for Starbucks pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from app.observability.logging import log_event
from app.pipelines.models import BronzeRecord
from app.storage.bronze.manifest_writer import write_manifest


@dataclass
class BronzeIngestResult:
    batch_id: str
    manifest_path: str
    record_count: int


def persist_bronze_batch(
    brand: str, records: Sequence[BronzeRecord], batch_id: str | None = None
) -> BronzeIngestResult:
    if not records:
        raise ValueError("No records to persist")
    batch_id = batch_id or datetime.utcnow().strftime("%Y%m%d%H%M%S")
    manifest_path = write_manifest(brand=brand, batch_id=batch_id, records=records)
    log_event(
        "bronze.persisted",
        brand=brand,
        batch_id=batch_id,
        record_count=len(records),
        manifest=str(manifest_path),
    )
    return BronzeIngestResult(
        batch_id=batch_id,
        manifest_path=str(manifest_path),
        record_count=len(records),
    )
