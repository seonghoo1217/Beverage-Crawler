"""Alerting helpers for dispatch latency and failures."""
from __future__ import annotations

from app.observability.logging import log_event
from app.observability.metrics import metrics

LATENCY_SLO_SECONDS = 300  # 5 minutes


def report_dispatch_latency(latency_seconds: float) -> None:
    metrics.set_gauge("spring_dispatch_latency_seconds", latency_seconds)
    if latency_seconds > LATENCY_SLO_SECONDS:
        log_event(
            "spring.dispatch_latency_violation",
            latency=latency_seconds,
            threshold=LATENCY_SLO_SECONDS,
        )


def notify_dispatch_failure(error: str, attempt: int) -> None:
    metrics.incr("spring_dispatch_failures")
    log_event("spring.dispatch_failed", attempt=attempt, error=error)


def notify_dispatch_success() -> None:
    metrics.incr("spring_dispatch_success")
    log_event("spring.dispatch_acknowledged")
