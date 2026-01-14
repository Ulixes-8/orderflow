"""Performance smoke tests for OrderFlow."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from conftest import parse_json_stdout, run_cli


def _base_env(db_path: Path) -> dict[str, str]:
    """Return base environment variables for CLI runs."""

    return {
        "ORDERFLOW_DB_PATH": str(db_path),
        "ORDERFLOW_AUTH_CODE": "123456",
    }


@pytest.mark.performance
def test_T_PERF_PLACE_001_place_smoke(artifact_collector, tmp_path: Path) -> None:
    """T-PERF-PLACE-001: measure mean/p95 for place."""

    db_path = tmp_path / "orders.db"
    env = _base_env(db_path)
    for _ in range(5):
        start = time.perf_counter()
        code, stdout, _ = run_cli(
            ["place", "--mobile", "+15551234567", "--message", "ORDER COFFEE=1"],
            cwd=Path.cwd(),
            env=env,
        )
        duration_ms = (time.perf_counter() - start) * 1000
        artifact_collector.record_performance("place", duration_ms)
        assert code == 0
        assert parse_json_stdout(stdout)["ok"] is True


@pytest.mark.performance
def test_T_PERF_BATCH_001_batch_smoke(artifact_collector, tmp_path: Path) -> None:
    """T-PERF-BATCH-001: record batch latency for derived throughput."""

    db_path = tmp_path / "orders.db"
    env = _base_env(db_path)
    batch_file = tmp_path / "batch.txt"
    # Fixed 2-line batch for stable latency-to-throughput derivation.
    batch_file.write_text(
        "+15551234567|ORDER COFFEE=1\n+15557654321|ORDER TEA=1\n",
        encoding="utf-8",
    )
    for _ in range(3):
        start = time.perf_counter()
        code, stdout, _ = run_cli(
            ["batch", "--input", str(batch_file)],
            cwd=Path.cwd(),
            env=env,
        )
        duration_ms = (time.perf_counter() - start) * 1000
        artifact_collector.record_performance("batch", duration_ms)
        assert code == 0
        lines = [json.loads(line) for line in stdout.strip().splitlines()]
        assert lines[-1]["command"] == "batch_summary"
