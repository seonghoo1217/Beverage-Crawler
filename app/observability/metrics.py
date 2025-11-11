"""Lightweight metrics collector for batch execution."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict


class MetricsRegistry:
    def __init__(self) -> None:
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}

    def incr(self, name: str, value: int = 1) -> None:
        self.counters[name] += value

    def set_gauge(self, name: str, value: float) -> None:
        self.gauges[name] = value

    def snapshot(self) -> dict:
        return {"counters": dict(self.counters), "gauges": dict(self.gauges)}


metrics = MetricsRegistry()
