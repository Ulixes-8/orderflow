"""In-memory repository implementation for OrderFlow."""

from __future__ import annotations

import copy
from typing import Dict, List

from orderflow.domain import Order, OrderStatus
from orderflow.store.base import (
    OrderAlreadyExistsError,
    OrderAlreadyFulfilledError,
    OrderNotFoundError,
)


class InMemoryOrderRepository:
    """In-memory implementation of the order repository protocol."""

    def __init__(self) -> None:
        """Initialize the in-memory store."""

        self._orders: Dict[str, Order] = {}

    def init_schema(self) -> None:
        """Initialize the in-memory store (no-op)."""

    def create_order(self, order: Order) -> None:
        """Persist a new order."""

        if order.order_id in self._orders:
            raise OrderAlreadyExistsError(f"Order {order.order_id} already exists.")
        self._orders[order.order_id] = copy.deepcopy(order)

    def get_order(self, order_id: str) -> Order | None:
        """Fetch an order by ID."""

        order = self._orders.get(order_id)
        return copy.deepcopy(order) if order else None

    def list_outstanding_grouped_by_mobile(self) -> Dict[str, List[Order]]:
        """List outstanding (pending) orders grouped by mobile."""

        pending_orders = [
            order
            for order in self._orders.values()
            if order.status == OrderStatus.PENDING
        ]
        pending_orders.sort(key=lambda order: (order.created_at_utc, order.order_id))
        grouped: Dict[str, List[Order]] = {}
        for order in pending_orders:
            grouped.setdefault(order.mobile, []).append(copy.deepcopy(order))
        return dict(sorted(grouped.items(), key=lambda item: item[0]))

    def fulfill_order(self, order_id: str, fulfilled_at_utc: str) -> Order:
        """Mark an order as fulfilled and return the updated order."""

        order = self._orders.get(order_id)
        if order is None:
            raise OrderNotFoundError(f"Order {order_id} not found.")
        if order.status == OrderStatus.FULFILLED:
            raise OrderAlreadyFulfilledError(f"Order {order_id} already fulfilled.")
        updated = Order(
            order_id=order.order_id,
            mobile=order.mobile,
            raw_message=order.raw_message,
            items=copy.deepcopy(order.items),
            status=OrderStatus.FULFILLED,
            created_at_utc=order.created_at_utc,
            fulfilled_at_utc=fulfilled_at_utc,
            total_pence=order.total_pence,
        )
        self._orders[order_id] = updated
        return copy.deepcopy(updated)
