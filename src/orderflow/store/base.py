"""Storage interfaces and exceptions for OrderFlow repositories."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Protocol

from orderflow.domain import Order


class OrderNotFoundError(Exception):
    """Raised when an order cannot be found in the repository."""


class OrderAlreadyFulfilledError(Exception):
    """Raised when attempting to fulfill an already fulfilled order."""


class OrderAlreadyExistsError(Exception):
    """Raised when attempting to create an order with a duplicate ID."""


class DatabaseError(Exception):
    """Raised when an underlying database error occurs."""


class OrderRepository(Protocol):
    """Protocol for order repositories."""

    def init_schema(self) -> None:
        """Initialize the repository schema."""

    def create_order(self, order: Order) -> None:
        """Persist a new order."""

    def get_order(self, order_id: str) -> Order | None:
        """Fetch an order by ID."""

    def list_outstanding_grouped_by_mobile(self) -> Dict[str, List[Order]]:
        """List outstanding (pending) orders grouped by mobile."""

    def fulfill_order(self, order_id: str, fulfilled_at_utc: str) -> Order:
        """Mark an order as fulfilled and return the updated order."""
