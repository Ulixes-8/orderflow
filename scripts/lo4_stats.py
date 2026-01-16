"""Statistics helpers for LO4 performance evidence."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from statistics import mean, median, pstdev
from typing import Iterable, List, Sequence, Tuple


@dataclass(frozen=True)
class BootstrapConfig:
    """Configuration for bootstrap resampling."""

    resamples: int
    seed: int = 0


def _percentile(sorted_samples: Sequence[float], pct: float) -> float:
    """Return the percentile using the nearest-rank method."""

    if not sorted_samples:
        return 0.0
    index = max(int(math.ceil(len(sorted_samples) * pct)) - 1, 0)
    return float(sorted_samples[index])


def _bootstrap_percentile(
    samples: Sequence[float],
    stat_fn,
    config: BootstrapConfig,
) -> Tuple[float, float]:
    """Compute percentile bootstrap CI for the given statistic."""

    rng = random.Random(config.seed)
    n = len(samples)
    if n == 0:
        return 0.0, 0.0
    stats: List[float] = []
    for _ in range(config.resamples):
        resample = [samples[rng.randrange(n)] for _ in range(n)]
        stats.append(stat_fn(resample))
    stats.sort()
    lower = _percentile(stats, 0.025)
    upper = _percentile(stats, 0.975)
    return lower, upper


def summarize_samples(
    samples: Sequence[float],
    bootstrap: BootstrapConfig,
) -> dict:
    """Summarize samples and compute bootstrap confidence intervals."""

    sorted_samples = sorted(samples)
    if not sorted_samples:
        return {
            "n": 0,
            "mean_ms": 0.0,
            "median_ms": 0.0,
            "stdev_ms": 0.0,
            "p95_ms": 0.0,
            "ci_mean_ms": [0.0, 0.0],
            "ci_p95_ms": [0.0, 0.0],
        }

    def _mean(values: Sequence[float]) -> float:
        return float(mean(values))

    def _p95(values: Sequence[float]) -> float:
        return float(_percentile(sorted(values), 0.95))

    ci_mean = _bootstrap_percentile(sorted_samples, _mean, bootstrap)
    ci_p95 = _bootstrap_percentile(sorted_samples, _p95, bootstrap)
    return {
        "n": len(sorted_samples),
        "mean_ms": round(mean(sorted_samples), 3),
        "median_ms": round(median(sorted_samples), 3),
        "stdev_ms": round(pstdev(sorted_samples), 3),
        "p95_ms": round(_percentile(sorted_samples, 0.95), 3),
        "ci_mean_ms": [round(ci_mean[0], 3), round(ci_mean[1], 3)],
        "ci_p95_ms": [round(ci_p95[0], 3), round(ci_p95[1], 3)],
    }
