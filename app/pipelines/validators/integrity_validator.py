"""Integrity guard rails before Spring dispatch."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence, Tuple

from app.config.settings import settings
from app.pipelines.models import SilverRecord


@dataclass
class IntegrityViolation:
    product_name: str
    brand: str
    size: str
    reason: str


@dataclass
class IntegrityReport:
    inspected: int = 0
    passed: int = 0
    blocked: list[IntegrityViolation] = field(default_factory=list)

    def track(self, record: SilverRecord, violation: str | None) -> None:
        self.inspected += 1
        if violation:
            self.blocked.append(
                IntegrityViolation(
                    product_name=record.product_name,
                    brand=record.brand,
                    size=record.size,
                    reason=violation,
                )
            )
            return
        self.passed += 1


def filter_valid_records(records: Iterable[SilverRecord]) -> tuple[list[SilverRecord], IntegrityReport]:
    """Drop records that violate brand size/type policies and build a report."""
    report = IntegrityReport()
    valid: list[SilverRecord] = []
    size_map = {
        "Starbucks": set(settings.starbucks.size_whitelist),
        "MegaCoffee": set(settings.megacoffee.size_whitelist),
    }

    for record in records:
        violation = None
        allowed_sizes = size_map.get(record.brand, set())
        if record.size not in allowed_sizes:
            violation = f"size {record.size} not allowed for {record.brand}"
        elif not record.beverage_type or record.beverage_type == "UNKNOWN":
            violation = "beverage_type missing"

        report.track(record, violation)
        if not violation:
            valid.append(record)

    return valid, report


def write_integrity_report(report: IntegrityReport, target: Path | None = None) -> Path:
    """Persist the integrity report for auditing."""
    target = target or Path("reports/integrity_report.md")
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Integrity Report",
        "",
        f"- Inspected: {report.inspected}",
        f"- Passed: {report.passed}",
        f"- Blocked: {len(report.blocked)}",
        "",
        "## Blocked Records",
    ]
    if not report.blocked:
        lines.append("없음")
    else:
        for violation in report.blocked:
            lines.append(
                f"- {violation.brand}/{violation.product_name} ({violation.size}): {violation.reason}"
            )
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target
