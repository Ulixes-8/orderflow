"""Domain models for the OrderFlow system."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class OrderStatus(str, Enum):
    """Enumeration of order states."""

    PENDING = "PENDING"
    FULFILLED = "FULFILLED"


@dataclass(frozen=True)
class CatalogueItem:
    """Represents a catalogue item available for ordering."""

    sku: str
    name: str
    unit_price_pence: int


@dataclass(frozen=True)
class OrderLine:
    """Represents a single line item within an order."""

    sku: str
    qty: int
    unit_price_pence: int
    line_total_pence: int


@dataclass(frozen=True)
class Order:
    """Represents a customer order with line items and totals."""

    order_id: str
    mobile: str
    raw_message: str
    items: List[OrderLine]
    status: OrderStatus
    created_at_utc: str
    fulfilled_at_utc: Optional[str]
    total_pence: int
