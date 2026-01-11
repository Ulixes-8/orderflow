"""Testing helpers for OrderFlow."""

from __future__ import annotations

from dataclasses import dataclass

from orderflow.auth import AuthService
from orderflow.catalogue import Catalogue
from orderflow.metrics import MetricsCollector
from orderflow.service import (
    Clock,
    IdGenerator,
    OrderService,
    ServiceLimits,
)
from orderflow.store.memory import InMemoryOrderRepository


@dataclass
class FixedClock:
    """Clock that returns a fixed UTC timestamp."""

    fixed_timestamp: str

    def now_utc_iso(self) -> str:
        return self.fixed_timestamp


class SequentialIdGenerator:
    """Sequential order ID generator for tests."""

    def __init__(self) -> None:
        """Initialize the sequential ID counter."""

        self._counter = 1

    def new_order_id(self) -> str:
        value = self._counter
        self._counter += 1
        return f"ORD-{value:08X}"


def make_test_service(
    catalogue_path: str | None = None, auth_code: str = "123456"
) -> OrderService:
    """Create a test OrderService with in-memory dependencies."""

    repository = InMemoryOrderRepository()
    repository.init_schema()
    catalogue = Catalogue.load(catalogue_path)
    auth = AuthService(auth_code)
    clock = FixedClock("2024-01-01T00:00:00Z")
    id_generator = SequentialIdGenerator()
    metrics = MetricsCollector()
    limits = ServiceLimits()
    return OrderService(
        repository=repository,
        catalogue=catalogue,
        auth_service=auth,
        clock=clock,
        id_generator=id_generator,
        metrics=metrics,
        limits=limits,
    )
