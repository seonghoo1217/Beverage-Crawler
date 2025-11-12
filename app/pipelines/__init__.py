"""Medallion pipeline orchestrator entrypoints."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.observability import alerts
from app.observability.logging import log_event
from app.observability.metrics import metrics
from app.ocr import collect_ocr_dataset
from app.pipelines.bronze_ingest import persist_bronze_batch
from app.pipelines.gold_publish import publish_gold_payload
from app.pipelines.merger import merge_brand_records, write_conflict_report
from app.pipelines.models import BronzeRecord, SilverRecord
from app.pipelines.publishers.spring_dispatcher import SpringDispatcher
from app.pipelines.publishers.spring_payload_builder import build_spring_payload
from app.pipelines.silver_transform import (
    convert_to_silver,
    generate_diff,
    persist_silver_records,
    write_change_log,
)
from app.pipelines.validators.dedup_validator import detect_duplicates
from app.pipelines.validators.integrity_validator import (
    filter_valid_records,
    write_integrity_report,
)
from app.storage.silver.snapshot import load_latest_snapshot
from app.starbucks_crawler import StarbucksCrawler, to_bronze_records
from app.megacoffee_crawler import (
    MegaCoffeeCrawler,
    to_bronze_records as mega_to_bronze_records,
)


@dataclass
class PipelineResult:
    batch_id: str
    status: str
    details: str


def run_medallion_batch(
    triggered_by: str = "manual", brands: list[str] | None = None
) -> PipelineResult:
    batch_id = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    brands = brands or ["Starbucks", "MegaCoffee"]
    results: list[PipelineResult] = []
    for brand in brands:
        if brand == "Starbucks":
            results.append(_run_starbucks(batch_id, triggered_by))
        elif brand == "MegaCoffee":
            results.append(_run_megacoffee(batch_id, triggered_by))
    overall_status = (
        "completed" if all(result.status == "completed" for result in results) else "partial"
    )
    details = "; ".join(result.details for result in results)
    _run_gold_stage(batch_id)
    return PipelineResult(batch_id=batch_id, status=overall_status, details=details)


def _run_starbucks(batch_id: str, triggered_by: str) -> PipelineResult:
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
        persist_silver_records("Starbucks", ingest_result.batch_id, silver_records)
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
            brand="Starbucks",
            batch_id=batch_id,
            triggered_by=triggered_by,
            record_count=len(bronze_records),
        )
        return PipelineResult(
            batch_id=batch_id,
            status="completed",
            details=f"Starbucks {len(silver_records)} records processed",
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        log_event("pipeline.failed", brand="Starbucks", batch_id=batch_id, error=str(exc))
        return PipelineResult(batch_id=batch_id, status="failed", details=f"Starbucks error: {exc}")


def _run_megacoffee(batch_id: str, triggered_by: str) -> PipelineResult:
    try:
        crawler = MegaCoffeeCrawler()
        items = crawler.fetch_all()
        bronze_records: list[BronzeRecord] = mega_to_bronze_records(items, batch_id=batch_id)
        ingest_result = persist_bronze_batch(
            brand="MegaCoffee", records=bronze_records, batch_id=batch_id
        )
        duplicate_report = detect_duplicates(bronze_records)
        silver_records, validation_summary = convert_to_silver(bronze_records)
        previous_snapshot = load_latest_snapshot("MegaCoffee")
        persist_silver_records("MegaCoffee", ingest_result.batch_id, silver_records)
        diff = generate_diff(previous_snapshot, silver_records)
        write_change_log(diff, Path("reports/megacoffee_change_log.md"))
        metrics.set_gauge(
            "megacoffee_crawl_success_rate",
            1.0 if not duplicate_report.warnings else 0.99,
        )
        log_event(
            "pipeline.completed",
            brand="MegaCoffee",
            batch_id=batch_id,
            triggered_by=triggered_by,
            record_count=len(bronze_records),
        )
        return PipelineResult(
            batch_id=batch_id,
            status="completed",
            details=f"MegaCoffee {len(silver_records)} records processed",
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        metrics.set_gauge("megacoffee_crawl_success_rate", 0)
        log_event("pipeline.failed", brand="MegaCoffee", batch_id=batch_id, error=str(exc))
        return PipelineResult(batch_id=batch_id, status="failed", details=f"MegaCoffee error: {exc}")


def _run_gold_stage(batch_id: str) -> None:
    """Merge, validate, and publish Gold tier payloads if inputs are ready."""
    silver_records = _collect_latest_silver_records()
    if not silver_records:
        return
    merge_result = merge_brand_records(silver_records)
    write_conflict_report(merge_result)
    valid_records, integrity_report = filter_valid_records(merge_result.records)
    write_integrity_report(integrity_report)
    if not valid_records:
        log_event(
            "pipeline.gold_skipped",
            batch_id=batch_id,
            reason="no valid records after integrity checks",
        )
        return
    payload = build_spring_payload(valid_records)
    dispatcher = SpringDispatcher()
    dispatch_result = dispatcher.dispatch(payload)
    alerts.notify_dispatch_success()
    publish_gold_payload(payload)
    log_event(
        "pipeline.gold_published",
        batch_id=batch_id,
        dispatch_attempts=dispatch_result.attempts,
        dispatch_latency=dispatch_result.latency_seconds,
        records=len(valid_records),
        conflicts=len(merge_result.conflicts),
        blocked=len(integrity_report.blocked),
    )


def _collect_latest_silver_records() -> dict[str, list[SilverRecord]]:
    records: dict[str, list[SilverRecord]] = {}
    for brand in ("Starbucks", "MegaCoffee"):
        snapshot = load_latest_snapshot(brand)
        if not snapshot:
            continue
        payloads = [
            SilverRecord.model_validate(record) for record in snapshot.get("records", [])
        ]
        if payloads:
            records[brand] = payloads
    return records
