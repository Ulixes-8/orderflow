"""System tests for OrderFlow CLI contract."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

import pytest

from orderflow.validation import (
    INVALID_MOBILE,
    MESSAGE_TOO_LONG,
    ORDER_NOT_FOUND,
    UNAUTHORIZED,
)
from conftest import parse_json_stdout, run_cli


def _base_env(db_path: Path) -> dict[str, str]:
    """Return base environment variables for CLI runs."""

    return {
        "ORDERFLOW_DB_PATH": str(db_path),
        "ORDERFLOW_AUTH_CODE": "123456",
    }


@pytest.mark.system
def test_T_SYS_PLACE_001_cli_place_success(tmp_path: Path, artifact_collector) -> None:
    """T-SYS-PLACE-001: end-to-end place returns ok and correct payload."""

    db_path = tmp_path / "orders.db"
    code, stdout, _ = run_cli(
        ["place", "--mobile", "+15551234567", "--message", "ORDER COFFEE=1"],
        cwd=Path.cwd(),
        env=_base_env(db_path),
    )
    assert code == 0
    payload = parse_json_stdout(stdout)
    assert payload["ok"] is True
    assert payload["command"] == "place"
    assert payload["data"]["status"] == "PENDING"


@pytest.mark.system
def test_T_SYS_ERRCODES_001_invalid_mobile_exit_2(tmp_path: Path, artifact_collector) -> None:
    """T-SYS-ERRCODES-001: invalid mobile returns INVALID_MOBILE and exit=2."""

    db_path = tmp_path / "orders.db"
    code, stdout, _ = run_cli(
        ["place", "--mobile", "1555", "--message", "ORDER COFFEE=1"],
        cwd=Path.cwd(),
        env=_base_env(db_path),
    )
    payload = parse_json_stdout(stdout)
    artifact_collector.record_error_code(payload["error"]["code"])
    assert code == 2
    assert payload["error"]["code"] == INVALID_MOBILE

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("SELECT COUNT(*) FROM orders").fetchone()
    assert rows is not None
    assert rows[0] == 0


@pytest.mark.system
def test_T_SYS_ERRCODES_002_message_too_long_exit_2(tmp_path: Path, artifact_collector) -> None:
    """T-SYS-ERRCODES-002: message too long returns MESSAGE_TOO_LONG."""

    db_path = tmp_path / "orders.db"
    long_message = "ORDER " + "A" * 300
    code, stdout, _ = run_cli(
        ["place", "--mobile", "+15551234567", "--message", long_message],
        cwd=Path.cwd(),
        env=_base_env(db_path),
    )
    payload = parse_json_stdout(stdout)
    artifact_collector.record_error_code(payload["error"]["code"])
    assert code == 2
    assert payload["error"]["code"] == MESSAGE_TOO_LONG

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("SELECT COUNT(*) FROM orders").fetchone()
    assert rows is not None
    assert rows[0] == 0


@pytest.mark.system
def test_T_SYS_LIST_001_list_returns_outstanding(tmp_path: Path) -> None:
    """T-SYS-LIST-001: list returns outstanding orders and count."""

    db_path = tmp_path / "orders.db"
    env = _base_env(db_path)
    run_cli(
        ["place", "--mobile", "+15551234567", "--message", "ORDER COFFEE=1"],
        cwd=Path.cwd(),
        env=env,
    )
    run_cli(
        ["place", "--mobile", "+15557654321", "--message", "ORDER TEA=1"],
        cwd=Path.cwd(),
        env=env,
    )
    code, stdout, _ = run_cli(["list"], cwd=Path.cwd(), env=env)
    assert code == 0
    payload = parse_json_stdout(stdout)
    assert payload["ok"] is True
    assert payload["data"]["outstanding_order_count"] == 2


@pytest.mark.system
def test_T_SYS_SHOW_001_show_returns_order_or_not_found(tmp_path: Path, artifact_collector) -> None:
    """T-SYS-SHOW-001: show returns order or ORDER_NOT_FOUND."""

    db_path = tmp_path / "orders.db"
    env = _base_env(db_path)
    _, stdout, _ = run_cli(
        ["place", "--mobile", "+15551234567", "--message", "ORDER COFFEE=1"],
        cwd=Path.cwd(),
        env=env,
    )
    order_id = parse_json_stdout(stdout)["data"]["order_id"]

    code, show_out, _ = run_cli(
        ["show", "--order-id", order_id],
        cwd=Path.cwd(),
        env=env,
    )
    assert code == 0
    payload = parse_json_stdout(show_out)
    assert payload["ok"] is True

    code, missing_out, _ = run_cli(
        ["show", "--order-id", "ORD-FFFFFFFF"],
        cwd=Path.cwd(),
        env=env,
    )
    payload = parse_json_stdout(missing_out)
    artifact_collector.record_error_code(payload["error"]["code"])
    assert code == 4
    assert payload["error"]["code"] == ORDER_NOT_FOUND


@pytest.mark.system
def test_T_SYS_BATCH_001_batch_emits_lines_and_summary(tmp_path: Path) -> None:
    """T-SYS-BATCH-001: batch emits per-line JSON and summary."""

    db_path = tmp_path / "orders.db"
    batch_file = tmp_path / "batch.txt"
    batch_file.write_text(
        "+15551234567|ORDER COFFEE=1\n+15557654321|ORDER TEA=1\n",
        encoding="utf-8",
    )
    code, stdout, _ = run_cli(
        ["batch", "--input", str(batch_file)],
        cwd=Path.cwd(),
        env=_base_env(db_path),
    )
    assert code == 0
    lines = [json.loads(line) for line in stdout.strip().splitlines()]
    assert lines[-1]["command"] == "batch_summary"
    assert lines[-1]["data"]["lines_processed"] == 2


@pytest.mark.system
def test_T_SYS_BATCH_002_batch_malformed_lines(tmp_path: Path, artifact_collector) -> None:
    """T-SYS-BATCH-002: malformed batch lines produce PARSE_ERROR."""

    db_path = tmp_path / "orders.db"
    batch_file = tmp_path / "batch.txt"
    batch_file.write_text("not a valid line\n", encoding="utf-8")
    code, stdout, _ = run_cli(
        ["batch", "--input", str(batch_file)],
        cwd=Path.cwd(),
        env=_base_env(db_path),
    )
    lines = [json.loads(line) for line in stdout.strip().splitlines()]
    error_code = lines[0]["response"]["error"]["code"]
    artifact_collector.record_error_code(error_code)
    assert code == 2
    assert error_code == "PARSE_ERROR"


@pytest.mark.system
def test_T_SYS_FULFILL_001_bad_auth_exit_3(tmp_path: Path, artifact_collector) -> None:
    """T-SYS-FULFILL-001: fulfill returns UNAUTHORIZED on bad auth."""

    db_path = tmp_path / "orders.db"
    env = _base_env(db_path)
    _, stdout, _ = run_cli(
        ["place", "--mobile", "+15551234567", "--message", "ORDER COFFEE=1"],
        cwd=Path.cwd(),
        env=env,
    )
    order_id = parse_json_stdout(stdout)["data"]["order_id"]

    code, stdout, _ = run_cli(
        ["fulfill", "--order-id", order_id, "--auth-code", "000000"],
        cwd=Path.cwd(),
        env=env,
    )
    payload = parse_json_stdout(stdout)
    artifact_collector.record_error_code(payload["error"]["code"])
    assert code == 3
    assert payload["error"]["code"] == UNAUTHORIZED


@pytest.mark.system
def test_T_SYS_LIVE_001_cli_returns_within_time(tmp_path: Path) -> None:
    """T-SYS-LIVE-001: CLI returns within bounded time."""

    db_path = tmp_path / "orders.db"
    start = time.perf_counter()
    code, stdout, _ = run_cli(["list"], cwd=Path.cwd(), env=_base_env(db_path))
    duration = time.perf_counter() - start
    assert code == 0
    assert duration < 2.0
    assert parse_json_stdout(stdout)["command"] == "list"


@pytest.mark.system
def test_T_SYS_OUTPUT_001_stdout_deterministic(tmp_path: Path) -> None:
    """T-SYS-OUTPUT-001: stdout JSON is deterministic."""

    db_path = tmp_path / "orders.db"
    env = _base_env(db_path)
    _, stdout1, _ = run_cli(["metrics"], cwd=Path.cwd(), env=env)
    _, stdout2, _ = run_cli(["metrics"], cwd=Path.cwd(), env=env)
    assert stdout1 == stdout2


@pytest.mark.system
def test_T_SYS_METRICS_001_metrics_schema_and_reset(tmp_path: Path) -> None:
    """T-SYS-METRICS-001: metrics output schema and reset semantics."""

    db_path = tmp_path / "orders.db"
    env = _base_env(db_path)
    run_cli(
        ["place", "--mobile", "+15551234567", "--message", "ORDER COFFEE=1"],
        cwd=Path.cwd(),
        env=env,
    )
    _, stdout, _ = run_cli(["metrics"], cwd=Path.cwd(), env=env)
    payload = parse_json_stdout(stdout)
    counters = payload["data"]["counters"]
    assert counters["messages_processed_total"] >= 1
    assert counters["orders_created_total"] >= 1

    run_cli(["metrics", "--reset"], cwd=Path.cwd(), env=env)
    _, stdout, _ = run_cli(["metrics"], cwd=Path.cwd(), env=env)
    payload = parse_json_stdout(stdout)
    counters = payload["data"]["counters"]
    assert counters["messages_processed_total"] == 0
    assert counters["orders_created_total"] == 0
