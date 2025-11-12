"""Send Spring delivery payloads with retry and alerting."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Optional

try:  # pragma: no cover - optional dependency is already declared
    import httpx
except ImportError:  # pragma: no cover - fallback when httpx missing in env
    httpx = None

from app.config.settings import settings
from app.observability import alerts
from app.observability.logging import log_event
from app.pipelines.models import DeliveryPayload


@dataclass
class DispatchResult:
    status: str
    attempts: int
    latency_seconds: float


class SpringDispatcher:
    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_token: Optional[str] = None,
        max_retries: int = 3,
        timeout_seconds: int = 10,
    ) -> None:
        self.endpoint = endpoint or getattr(settings, "spring_endpoint", "")
        self.api_token = api_token or getattr(settings, "spring_api_token", "")
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds

    def dispatch(self, payload: DeliveryPayload) -> DispatchResult:
        body = payload.model_dump(mode="json")
        attempts = 0
        last_exc: Exception | None = None
        while attempts < self.max_retries:
            attempts += 1
            start = time.monotonic()
            try:
                self._send(body)
                latency = time.monotonic() - start
                alerts.report_dispatch_latency(latency)
                log_event(
                    "spring.dispatch_success",
                    attempts=attempts,
                    latency=latency,
                    endpoint=self.endpoint or "file",
                )
                return DispatchResult(status="success", attempts=attempts, latency_seconds=latency)
            except Exception as exc:  # pragma: no cover - defensive branch
                last_exc = exc
                alerts.notify_dispatch_failure(str(exc), attempt=attempts)
                if attempts >= self.max_retries:
                    break
                time.sleep(min(2**attempts, 5))
        raise RuntimeError(f"Spring dispatch failed after {attempts} attempts") from last_exc

    def _send(self, body: dict) -> None:
        if not self.endpoint:
            # No endpoint configured yet; treat as dry-run and log the payload size.
            log_event("spring.dispatch_dryrun", bytes=len(json.dumps(body)))
            return
        if httpx is None:
            raise RuntimeError("httpx is required for real Spring dispatches")
        headers = {"Content-Type": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        response = httpx.post(
            self.endpoint,
            json=body,
            headers=headers,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
