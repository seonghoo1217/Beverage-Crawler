"""Medallion pipeline orchestrator entrypoints."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.observability.logging import log_event
from app.ocr import collect_ocr_dataset
from app.pipelines.bronze_ingest import persist_bronze_batch
from app.pipelines.models import BronzeRecord
from app.pipelines.silver_transform import convert_to_silver
from app.pipelines.validators.dedup_validator import detect_duplicates
from app.starbucks_crawler import StarbucksCrawler, to_bronze_records


@dataclass
class PipelineResult:
    batch_id: str
    status: str
    details: str


def run_medallion_batch(triggered_by: str = "manual") -> PipelineResult:
    batch_id = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    try:
        crawler = StarbucksCrawler()
        items = crawler.fetch_all()
        ocr_dataset = collect_ocr_dataset()
        bronze_records: list[BronzeRecord] = to_bronze_records(
            items, batch_id=batch_id, ocr_lookup=ocr_dataset
        )
        ingest_result = persist_bronze_batch(
            brand="Starbucks", records=bronze_records, batch_id=batch_id
        )
        duplicate_report = detect_duplicates(bronze_records)
        silver_records, validation_summary = convert_to_silver(bronze_records)
        from reports.starbucks_quality_report import (
            StarbucksQualityContext,
            render_quality_report,
        )

        render_quality_report(
            StarbucksQualityContext(
                batch_id=ingest_result.batch_id,
                summary=validation_summary,
                duplicates=duplicate_report,
            )
        )
        log_event(
            "pipeline.completed",
            batch_id=batch_id,
            triggered_by=triggered_by,
            record_count=len(bronze_records),
        )
        return PipelineResult(
            batch_id=batch_id,
            status="completed",
            details=f"Processed {len(silver_records)} Starbucks beverages",
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        log_event("pipeline.failed", batch_id=batch_id, error=str(exc))
        return PipelineResult(batch_id=batch_id, status="failed", details=str(exc))
