"""SQLite repository implementation for OrderFlow."""

from __future__ import annotations

import sqlite3
from typing import Dict, List, Sequence

from orderflow.domain import Order, OrderLine, OrderStatus
from orderflow.store.base import (
    DatabaseError,
    OrderAlreadyExistsError,
    OrderAlreadyFulfilledError,
    OrderNotFoundError,
)


class SQLiteOrderRepository:
    """SQLite implementation of the order repository protocol."""

    def __init__(self, db_path: str) -> None:
        """Initialize the repository with the provided database path."""

        self._db_path = db_path

    def init_schema(self) -> None:
        """Initialize the SQLite schema if it does not exist."""

        try:
            with self._connect() as conn:
                conn.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS orders (
                        order_id TEXT PRIMARY KEY,
                        mobile TEXT NOT NULL,
                        raw_message TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at_utc TEXT NOT NULL,
                        fulfilled_at_utc TEXT NULL,
                        total_pence INTEGER NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS order_lines (
                        order_id TEXT NOT NULL,
                        sku TEXT NOT NULL,
                        qty INTEGER NOT NULL,
                        unit_price_pence INTEGER NOT NULL,
                        line_total_pence INTEGER NOT NULL,
                        PRIMARY KEY (order_id, sku),
                        FOREIGN KEY (order_id)
                            REFERENCES orders(order_id)
                            ON DELETE CASCADE
                    );
                    """
                )
        except sqlite3.Error as exc:
            raise DatabaseError("Failed to initialize schema.") from exc

    def create_order(self, order: Order) -> None:
        """Persist a new order and its line items."""

        try:
            with self._connect() as conn:
                if self._order_exists(conn, order.order_id):
                    raise OrderAlreadyExistsError(
                        f"Order {order.order_id} already exists."
                    )
                conn.execute(
                    """
                    INSERT INTO orders (
                        order_id,
                        mobile,
                        raw_message,
                        status,
                        created_at_utc,
                        fulfilled_at_utc,
                        total_pence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        order.order_id,
                        order.mobile,
                        order.raw_message,
                        order.status.value,
                        order.created_at_utc,
                        order.fulfilled_at_utc,
                        order.total_pence,
                    ),
                )
                conn.executemany(
                    """
                    INSERT INTO order_lines (
                        order_id,
                        sku,
                        qty,
                        unit_price_pence,
                        line_total_pence
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            order.order_id,
                            line.sku,
                            line.qty,
                            line.unit_price_pence,
                            line.line_total_pence,
                        )
                        for line in order.items
                    ],
                )
        except OrderAlreadyExistsError:
            raise
        except sqlite3.Error as exc:
            raise DatabaseError("Failed to create order.") from exc

    def get_order(self, order_id: str) -> Order | None:
        """Fetch an order by ID."""

        try:
            with self._connect() as conn:
                order_row = conn.execute(
                    """
                    SELECT * FROM orders WHERE order_id = ?
                    """,
                    (order_id,),
                ).fetchone()
                if order_row is None:
                    return None
                lines = self._fetch_lines(conn, order_id)
                return _order_from_rows(order_row, lines)
        except sqlite3.Error as exc:
            raise DatabaseError("Failed to fetch order.") from exc

    def list_outstanding_grouped_by_mobile(self) -> Dict[str, List[Order]]:
        """List outstanding (pending) orders grouped by mobile."""

        try:
            with self._connect() as conn:
                order_rows = conn.execute(
                    """
                    SELECT * FROM orders
                    WHERE status = ?
                    ORDER BY created_at_utc ASC, order_id ASC
                    """,
                    (OrderStatus.PENDING.value,),
                ).fetchall()
                orders: List[Order] = []
                for order_row in order_rows:
                    lines = self._fetch_lines(conn, order_row["order_id"])
                    orders.append(_order_from_rows(order_row, lines))
                grouped: Dict[str, List[Order]] = {}
                for order in orders:
                    grouped.setdefault(order.mobile, []).append(order)
                return dict(sorted(grouped.items(), key=lambda item: item[0]))
        except sqlite3.Error as exc:
            raise DatabaseError("Failed to list outstanding orders.") from exc

    def fulfill_order(self, order_id: str, fulfilled_at_utc: str) -> Order:
        """Mark an order as fulfilled and return the updated order."""

        try:
            with self._connect() as conn:
                order_row = conn.execute(
                    """
                    SELECT * FROM orders WHERE order_id = ?
                    """,
                    (order_id,),
                ).fetchone()
                if order_row is None:
                    raise OrderNotFoundError(f"Order {order_id} not found.")
                if order_row["status"] == OrderStatus.FULFILLED.value:
                    raise OrderAlreadyFulfilledError(
                        f"Order {order_id} already fulfilled."
                    )
                conn.execute(
                    """
                    UPDATE orders
                    SET status = ?, fulfilled_at_utc = ?
                    WHERE order_id = ?
                    """,
                    (OrderStatus.FULFILLED.value, fulfilled_at_utc, order_id),
                )
                lines = self._fetch_lines(conn, order_id)
                updated_row = dict(order_row)
                updated_row["status"] = OrderStatus.FULFILLED.value
                updated_row["fulfilled_at_utc"] = fulfilled_at_utc
                return _order_from_rows(updated_row, lines)
        except (OrderNotFoundError, OrderAlreadyFulfilledError):
            raise
        except sqlite3.Error as exc:
            raise DatabaseError("Failed to fulfill order.") from exc

    def _connect(self) -> sqlite3.Connection:
        """Create a SQLite connection with foreign keys enabled."""

        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _order_exists(self, conn: sqlite3.Connection, order_id: str) -> bool:
        """Return True if the order exists in the database."""

        row = conn.execute(
            "SELECT 1 FROM orders WHERE order_id = ?", (order_id,)
        ).fetchone()
        return row is not None

    def _fetch_lines(
        self, conn: sqlite3.Connection, order_id: str
    ) -> Sequence[sqlite3.Row]:
        """Fetch order line rows for a specific order."""

        return conn.execute(
            """
            SELECT * FROM order_lines WHERE order_id = ?
            ORDER BY sku ASC
            """,
            (order_id,),
        ).fetchall()


def _order_from_rows(order_row: sqlite3.Row | dict, line_rows: Sequence[sqlite3.Row]) -> Order:
    """Build an Order dataclass from row data."""

    items = [
        OrderLine(
            sku=line_row["sku"],
            qty=int(line_row["qty"]),
            unit_price_pence=int(line_row["unit_price_pence"]),
            line_total_pence=int(line_row["line_total_pence"]),
        )
        for line_row in line_rows
    ]
    return Order(
        order_id=order_row["order_id"],
        mobile=order_row["mobile"],
        raw_message=order_row["raw_message"],
        items=items,
        status=OrderStatus(order_row["status"]),
        created_at_utc=order_row["created_at_utc"],
        fulfilled_at_utc=order_row["fulfilled_at_utc"],
        total_pence=int(order_row["total_pence"]),
    )
