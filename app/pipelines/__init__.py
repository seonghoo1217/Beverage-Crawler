"""Medallion pipeline orchestrator entrypoints."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class PipelineResult:
    batch_id: str
    status: str
    details: str


def run_medallion_batch(triggered_by: str = "manual") -> PipelineResult:
    """Placeholder orchestration hook until full pipeline is implemented."""
    batch_id = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    # TODO: hook into bronze/silver/gold modules when ready
    return PipelineResult(
        batch_id=batch_id,
        status="queued",
        details=f"Pipeline trigger recorded by {triggered_by}",
    )
