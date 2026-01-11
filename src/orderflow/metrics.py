"""Metrics collection and timing utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import median
import math
import time
from typing import Dict, List


@dataclass
class MetricsCollector:
    """Collect counters and timing samples for OrderFlow."""

    messages_processed_total: int = 0
    orders_created_total: int = 0
    orders_rejected_total: int = 0
    orders_fulfilled_total: int = 0
    errors_total: int = 0
    errors_by_code: Dict[str, int] = field(default_factory=dict)
    parse_ms: List[float] = field(default_factory=list)
    store_ms: List[float] = field(default_factory=list)
    total_ms: List[float] = field(default_factory=list)

    def increment_error(self, code: str) -> None:
        """Increment error counters for a specific code."""

        self.errors_total += 1
        self.errors_by_code[code] = self.errors_by_code.get(code, 0) + 1

    def reset(self) -> None:
        """Reset all counters and timing samples."""

        self.messages_processed_total = 0
        self.orders_created_total = 0
        self.orders_rejected_total = 0
        self.orders_fulfilled_total = 0
        self.errors_total = 0
        self.errors_by_code = {}
        self.parse_ms = []
        self.store_ms = []
        self.total_ms = []

    def record_timing(self, series: str, duration_ms: float) -> None:
        """Record a timing sample for the given series."""

        samples = getattr(self, series)
        samples.append(duration_ms)

    def summary(self) -> Dict[str, Dict[str, float | int]]:
        """Return deterministic summary statistics for timing series."""

        return {
            "parse_ms": _summarize(self.parse_ms),
            "store_ms": _summarize(self.store_ms),
            "total_ms": _summarize(self.total_ms),
        }


class TimingContext:
    """Context manager for timing blocks in milliseconds."""

    def __init__(self, metrics: MetricsCollector, series: str) -> None:
        """Initialize the timing context manager."""

        self._metrics = metrics
        self._series = series
        self._start: float | None = None

    def __enter__(self) -> "TimingContext":
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._start is None:
            return
        duration_ms = (time.perf_counter() - self._start) * 1000
        self._metrics.record_timing(self._series, duration_ms)


def _summarize(samples: List[float]) -> Dict[str, float | int]:
    """Summarize timing samples with deterministic rounding."""

    if not samples:
        return {
            "count": 0,
            "mean_ms": 0.0,
            "p50_ms": 0.0,
            "p95_ms": 0.0,
            "min_ms": 0.0,
            "max_ms": 0.0,
        }
    sorted_samples = sorted(samples)
    count = len(sorted_samples)
    mean = sum(sorted_samples) / count
    p50 = median(sorted_samples)
    p95_index = max(math.ceil(count * 0.95) - 1, 0)
    p95 = sorted_samples[min(p95_index, count - 1)]
    return {
        "count": count,
        "mean_ms": round(mean, 3),
        "p50_ms": round(p50, 3),
        "p95_ms": round(p95, 3),
        "min_ms": round(sorted_samples[0], 3),
        "max_ms": round(sorted_samples[-1], 3),
    }
