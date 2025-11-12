"""Create sanitized Gold tier payloads for public APIs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config.settings import settings
from app.pipelines.models import DeliveryPayload


def publish_gold_payload(payload: DeliveryPayload) -> Path:
    """Persist a public-friendly payload without internal identifiers."""
    sanitized = _sanitize(payload)
    gold_dir = settings.storage_root / "gold"
    gold_dir.mkdir(parents=True, exist_ok=True)
    timestamp = payload.generated_at.strftime("%Y%m%d%H%M%S")
    snapshot_path = gold_dir / f"{timestamp}.json"
    snapshot_path.write_text(json.dumps(sanitized, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_path = gold_dir / "latest.json"
    latest_path.write_text(json.dumps(sanitized, ensure_ascii=False, indent=2), encoding="utf-8")
    return latest_path


def _sanitize(payload: DeliveryPayload) -> dict[str, Any]:
    serialized = payload.model_dump(mode="json")
    for brand in serialized.get("brands", []):
        for item in brand.get("items", []):
            item.pop("productId", None)
            item.pop("isLiked", None)
    return serialized
