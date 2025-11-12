"""Generate Starbucks quality report markdown."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from app.pipelines.validators.dedup_validator import DuplicateReport
from app.pipelines.validators.starbucks_validator import StarbucksValidationSummary


@dataclass
class StarbucksQualityContext:
    batch_id: str
    summary: StarbucksValidationSummary
    duplicates: DuplicateReport | None = None


def render_quality_report(context: StarbucksQualityContext, output_path: Path | None = None) -> Path:
    output_path = output_path or Path("reports/starbucks_quality_report.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    duplicate_section = ""
    if context.duplicates:
        duplicate_section = (
            f"- Duplicates: {context.duplicates.duplicates or ['없음']}\n"
            f"- Checksum issues: {context.duplicates.checksum_mismatches or ['없음']}\n"
        )
    content = f"""# Starbucks Quality Report

**Batch**: {context.batch_id}

## Validation Summary
- Total inspected: {context.summary.inspected}
- Clean records: {context.summary.clean}
- Needs review: {context.summary.needs_review}
{duplicate_section if duplicate_section else ''}

## Offenders
{os.linesep.join(f'- {name}' for name in context.summary.offenders) if context.summary.offenders else '없음'}
"""
    output_path.write_text(content.strip() + "\n", encoding="utf-8")
    return output_path
