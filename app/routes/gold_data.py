"""Expose Gold tier payloads through HTTP."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.config.settings import settings

router = APIRouter(prefix="/api/v1/gold", tags=["Gold"])


@router.get("/latest", summary="Latest Gold payload")
def fetch_latest_gold_payload() -> dict:
    payload = read_latest_gold_payload()
    if payload is None:
        raise HTTPException(status_code=404, detail="Gold payload not available yet")
    return payload


def read_latest_gold_payload() -> dict | None:
    path = _latest_gold_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_gold_path() -> Path:
    return settings.storage_root / "gold" / "latest.json"
