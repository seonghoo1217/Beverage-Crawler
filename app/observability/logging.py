"""Structured logging helpers for pipeline runs."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger("pipeline")
logging.basicConfig(level=logging.INFO, format="%(message)s")


def log_event(event: str, **fields: Any) -> None:
    payload = {"timestamp": datetime.utcnow().isoformat(), "event": event, **fields}
    logger.info(json.dumps(payload, ensure_ascii=False))
