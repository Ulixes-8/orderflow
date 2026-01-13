"""Integration tests for service and SQLite repository."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from orderflow.auth import AuthService
from orderflow.catalogue import Catalogue
from orderflow.diagnostics import NullDiagnosticsSink
from orderflow.metrics import MetricsCollector
from orderflow.service import OrderService, ServiceLimits
from orderflow.store.sqlite import SQLiteOrderRepository
from orderflow.testing_helpers import FixedClock, SequentialIdGenerator
from orderflow.validation import DATABASE_ERROR, INVALID_MOBILE, ORDER_ALREADY_FULFILLED, UNAUTHORIZED


def _build_sqlite_service(db_path: Path) -> OrderService:
    """Build a service backed by SQLite for integration tests."""

    repository = SQLiteOrderRepository(str(db_path))
    repository.init_schema()
    return OrderService(
        repository=repository,
        catalogue=Catalogue.load(None),
        auth_service=AuthService("123456"),
        clock=FixedClock("2024-01-01T00:00:00Z"),
        id_generator=SequentialIdGenerator(),
        metrics=MetricsCollector(),
        diagnostics=NullDiagnosticsSink(),
        limits=ServiceLimits(),
    )


@pytest.mark.integration
def test_T_INT_PLACE_001_service_persists_order(tmp_path: Path) -> None:
    """T-INT-PLACE-001: service + repo persists correct order state."""

    db_path = tmp_path / "orders.db"
    service = _build_sqlite_service(db_path)

    response = service.place_order("+15551234567", "ORDER COFFEE=2")
    assert response["ok"] is True
    order_id = response["data"]["order_id"]

    repo = SQLiteOrderRepository(str(db_path))
    order = repo.get_order(order_id)
    assert order is not None
    assert order.status.value == "PENDING"
    assert order.total_pence > 0


@pytest.mark.integration
def test_T_INT_LIST_001_grouped_outstanding_orders(tmp_path: Path) -> None:
    """T-INT-LIST-001: repo groups pending orders by mobile."""

    db_path = tmp_path / "orders.db"
    service = _build_sqlite_service(db_path)

    service.place_order("+15551234567", "ORDER COFFEE=1")
    service.place_order("+15551234567", "ORDER TEA=1")
    service.place_order("+15557654321", "ORDER JUICE=1")

    repo = SQLiteOrderRepository(str(db_path))
    grouped = repo.list_outstanding_grouped_by_mobile()
    assert list(grouped.keys()) == ["+15551234567", "+15557654321"]
    assert len(grouped["+15551234567"]) == 2
    assert len(grouped["+15557654321"]) == 1


@pytest.mark.integration
def test_T_INT_SHOW_001_retrieves_stored_order(tmp_path: Path) -> None:
    """T-INT-SHOW-001: repo retrieves stored order deterministically."""

    db_path = tmp_path / "orders.db"
    service = _build_sqlite_service(db_path)

    response = service.place_order("+15551234567", "ORDER COFFEE=1")
    order_id = response["data"]["order_id"]

    repo = SQLiteOrderRepository(str(db_path))
    order = repo.get_order(order_id)
    assert order is not None
    assert order.order_id == order_id


@pytest.mark.integration
def test_T_INT_FULFILL_001_wrong_auth_no_transition(tmp_path: Path) -> None:
    """T-INT-FULFILL-001: wrong auth causes no persisted transition."""

    db_path = tmp_path / "orders.db"
    service = _build_sqlite_service(db_path)

    response = service.place_order("+15551234567", "ORDER COFFEE=1")
    order_id = response["data"]["order_id"]
    response = service.fulfill_order(order_id, "000000")

    assert response["ok"] is False
    assert response["error"]["code"] == UNAUTHORIZED

    repo = SQLiteOrderRepository(str(db_path))
    order = repo.get_order(order_id)
    assert order is not None
    assert order.status.value == "PENDING"


@pytest.mark.integration
def test_T_INT_FULFILL_002_second_fulfill_rejected(tmp_path: Path) -> None:
    """T-INT-FULFILL-002: second fulfill rejected with no state change."""

    db_path = tmp_path / "orders.db"
    service = _build_sqlite_service(db_path)

    response = service.place_order("+15551234567", "ORDER COFFEE=1")
    order_id = response["data"]["order_id"]
    first = service.fulfill_order(order_id, "123456")
    assert first["ok"] is True

    second = service.fulfill_order(order_id, "123456")
    assert second["ok"] is False
    assert second["error"]["code"] == ORDER_ALREADY_FULFILLED

    repo = SQLiteOrderRepository(str(db_path))
    order = repo.get_order(order_id)
    assert order is not None
    assert order.status.value == "FULFILLED"


@pytest.mark.integration
def test_T_INT_SEC_001_sql_injection_input_no_schema_change(tmp_path: Path) -> None:
    """T-INT-SEC-001: SQL injection strings do not alter schema."""

    db_path = tmp_path / "orders.db"
    service = _build_sqlite_service(db_path)

    response = service.place_order("+1555'; DROP TABLE orders;--", "ORDER COFFEE=1")
    assert response["ok"] is False
    assert response["error"]["code"] == INVALID_MOBILE

    with sqlite3.connect(db_path) as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    table_names = {row[0] for row in tables}
    assert "orders" in table_names
    assert "order_lines" in table_names


@pytest.mark.integration
def test_T_INT_DB_FAIL_001_database_error_no_partial_writes(tmp_path: Path) -> None:
    """T-INT-DB-FAIL-001: simulated DB error returns DATABASE_ERROR."""

    db_path = tmp_path / "orders.db"
    service = _build_sqlite_service(db_path)

    repo = SQLiteOrderRepository(str(db_path))
    repo.init_schema()

    with sqlite3.connect(db_path) as conn:
        conn.execute("DROP TABLE order_lines")

    response = service.place_order("+15551234567", "ORDER COFFEE=1")
    assert response["ok"] is False
    assert response["error"]["code"] == DATABASE_ERROR

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("SELECT COUNT(*) FROM orders").fetchone()
    assert rows is not None
    assert rows[0] == 0
