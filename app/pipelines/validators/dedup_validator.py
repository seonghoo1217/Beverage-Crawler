"""Duplicate + checksum validation utilities for medallion pipeline."""
from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from app.pipelines.models import BronzeRecord


@dataclass
class DuplicateReport:
    duplicates: list[str]
    checksum_mismatches: list[str]
    warnings: list[str]


def calculate_checksum(payload: dict) -> str:
    """Deterministic checksum for raw payload dictionaries."""
    serialized = repr(sorted(payload.items())).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def detect_duplicates(records: Iterable[BronzeRecord]) -> DuplicateReport:
    key_map: dict[tuple[str, str], list[BronzeRecord]] = defaultdict(list)
    checksum_mismatches: list[str] = []

    for record in records:
        key = (record.product_name.lower(), record.size)
        key_map[key].append(record)
        expected_checksum = record.source.checksum
        actual_checksum = calculate_checksum(record.nutrition_raw)
        if actual_checksum != expected_checksum:
            checksum_mismatches.append(record.product_name)

    duplicates = [f"{name}/{size}" for (name, size), items in key_map.items() if len(items) > 1]
    warnings: list[str] = []
    if duplicates:
        warnings.append("Duplicated product_name+size combinations detected")
    if checksum_mismatches:
        warnings.append("Checksum mismatches found in bronze payloads")

    return DuplicateReport(duplicates=duplicates, checksum_mismatches=checksum_mismatches, warnings=warnings)
