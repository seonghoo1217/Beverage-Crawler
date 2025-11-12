"""Merge brand-specific Silver tier snapshots into a consolidated view."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from app.observability.logging import log_event
from app.pipelines.models import SilverRecord


@dataclass
class MergeConflict:
    """Represents a duplicate product_name+size combination discovered during merge."""

    key: str
    brands: list[str]
    reason: str


@dataclass
class MergeResult:
    records: list[SilverRecord]
    conflicts: list[MergeConflict] = field(default_factory=list)


def merge_brand_records(brand_records: Mapping[str, Sequence[SilverRecord]]) -> MergeResult:
    """Merge records coming from each brand while removing duplicates.

    Duplicates are determined by case-insensitive (product_name, size) pairs.
    When a collision happens the first-seen record wins and the conflict list
    captures which brands were involved so auditors can review the decision.
    """
    seen: dict[str, SilverRecord] = {}
    conflicts: list[MergeConflict] = []
    merged: list[SilverRecord] = []

    for brand, records in brand_records.items():
        for record in records:
            key = _dedupe_key(record.product_name, record.size)
            if key in seen:
                conflicts.append(
                    MergeConflict(
                        key=key,
                        brands=[seen[key].brand, brand],
                        reason="duplicate product_name+size",
                    )
                )
                log_event(
                    "merge.duplicate_detected",
                    key=key,
                    existing_brand=seen[key].brand,
                    conflicting_brand=brand,
                )
                continue
            seen[key] = record
            merged.append(record)

    return MergeResult(records=merged, conflicts=conflicts)


def write_conflict_report(result: MergeResult, target: Path | None = None) -> Path:
    """Persist a markdown report summarizing merge conflicts."""
    target = target or Path("reports/merge_conflicts.md")
    target.parent.mkdir(parents=True, exist_ok=True)
    if not result.conflicts:
        target.write_text("# Merge Conflicts\n\n충돌이 발견되지 않았습니다.\n", encoding="utf-8")
        return target

    lines = ["# Merge Conflicts", ""]
    for conflict in result.conflicts:
        lines.append(
            f"- `{conflict.key}`: brands={', '.join(conflict.brands)}, reason={conflict.reason}"
        )
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def _dedupe_key(product_name: str, size: str) -> str:
    return f"{product_name.strip().lower()}::{size}"
