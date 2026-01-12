"""Service layer implementing OrderFlow business logic."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from typing import Dict, List, Protocol

from orderflow.auth import AuthService
from orderflow.catalogue import Catalogue
from orderflow.diagnostics import DiagnosticsSink, NullDiagnosticsSink
from orderflow.domain import Order, OrderLine, OrderStatus
from orderflow.metrics import MetricsCollector, TimingContext
from orderflow.parser import parse_order_message
from orderflow.store.base import (
    DatabaseError,
    OrderAlreadyExistsError,
    OrderAlreadyFulfilledError,
    OrderNotFoundError,
    OrderRepository,
)
from orderflow.validation import (
    DATABASE_ERROR,
    INTERNAL_ERROR,
    ORDER_ALREADY_FULFILLED,
    ORDER_NOT_FOUND,
    UNAUTHORIZED,
    UNKNOWN_ITEM,
    ValidationError,
    validate_auth_code_format,
    validate_message_length,
    validate_mobile,
    validate_order_id,
)

_logger = logging.getLogger(__name__)


class Clock(Protocol):
    """Protocol for time providers."""

    def now_utc_iso(self) -> str:
        """Return current UTC timestamp formatted as ISO8601."""


class IdGenerator(Protocol):
    """Protocol for order ID generation."""

    def new_order_id(self) -> str:
        """Generate a new order ID."""


class SystemClock:
    """Clock implementation using system UTC time."""

    def now_utc_iso(self) -> str:
        """Return the current UTC time as an ISO8601 string."""

        now = datetime.now(timezone.utc).replace(microsecond=0)
        return now.strftime("%Y-%m-%dT%H:%M:%SZ")


class RandomIdGenerator:
    """Random order ID generator using secure random tokens."""

    def new_order_id(self) -> str:
        """Generate a new order ID."""

        import secrets

        return f"ORD-{secrets.token_hex(4).upper()}"


@dataclass
class ServiceLimits:
    """Configuration limits for the OrderFlow service."""

    max_message_len: int = 256
    max_items: int = 20
    max_qty: int = 99


class OrderService:
    """Service for managing orders."""

    def __init__(
        self,
        repository: OrderRepository,
        catalogue: Catalogue,
        auth_service: AuthService,
        clock: Clock,
        id_generator: IdGenerator,
        metrics: MetricsCollector,
        diagnostics: DiagnosticsSink | None = None,
        limits: ServiceLimits | None = None,
    ) -> None:
        self._repository = repository
        self._catalogue = catalogue
        self._auth_service = auth_service
        self._clock = clock
        self._id_generator = id_generator
        self._metrics = metrics
        self._diagnostics = diagnostics or NullDiagnosticsSink()
        self._limits = limits or ServiceLimits()

    def place_order(self, mobile: str, message: str) -> Dict[str, object]:
        """Place a new order and return a response dict."""

        self._metrics.messages_processed_total += 1
        self._diagnostics.record("place.start", {"mobile": mobile, "message_len": len(message.rstrip("\n"))})
        with TimingContext(self._metrics, "total_ms"):
            try:
                canonical_mobile = validate_mobile(mobile)
                self._diagnostics.record("place.mobile_ok", {"mobile": canonical_mobile})
                validate_message_length(message, self._limits.max_message_len)
                with TimingContext(self._metrics, "parse_ms"):
                    sku_quantities = parse_order_message(
                        message,
                        max_items=self._limits.max_items,
                        max_qty=self._limits.max_qty,
                    )
                    self._diagnostics.record("place.parsed", {"sku_count": len(sku_quantities), "skus": sorted(sku_quantities)})
                    for sku in sku_quantities:
                        if not self._catalogue.has(sku):
                            raise ValidationError(
                                UNKNOWN_ITEM,
                                "Unknown SKU in order message.",
                                details={"sku": sku},
                            )
                    items = self._build_order_lines(sku_quantities)
                order = self._build_order(canonical_mobile, message, items)
                self._ensure_order_invariants(order)
                with TimingContext(self._metrics, "store_ms"):
                    order = self._create_order_with_retry(order)
                self._metrics.orders_created_total += 1
                self._diagnostics.record("place.stored", {"order_id": order.order_id, "total_pence": order.total_pence})
                return {
                    "ok": True,
                    "command": "place",
                    "data": _order_payload(order),
                }
            except ValidationError as exc:
                return self._error_response("place", exc)
            except OrderAlreadyExistsError:
                return self._error_response(
                    "place",
                    ValidationError(INTERNAL_ERROR, "Order ID collision."),
                )
            except DatabaseError as exc:
                _logger.exception("Database error during place")
                return self._error_response(
                    "place",
                    ValidationError(DATABASE_ERROR, "Database error.")
                )
            except Exception as exc:
                _logger.exception("Unhandled error during place")
                return self._error_response(
                    "place",
                    ValidationError(INTERNAL_ERROR, "Internal error."),
                )

    def list_outstanding(self) -> Dict[str, object]:
        """List outstanding orders grouped by mobile."""

        with TimingContext(self._metrics, "total_ms"):
            try:
                grouped = self._repository.list_outstanding_grouped_by_mobile()
                outstanding: List[Dict[str, object]] = []
                total_count = 0
                for mobile, orders in grouped.items():
                    order_views = []
                    for order in orders:
                        order_views.append(
                            {
                                "order_id": order.order_id,
                                "created_at_utc": order.created_at_utc,
                                "total_pence": order.total_pence,
                                "items": [
                                    {"sku": line.sku, "qty": line.qty}
                                    for line in order.items
                                ],
                            }
                        )
                    total_count += len(order_views)
                    outstanding.append({"mobile": mobile, "orders": order_views})
                return {
                    "ok": True,
                    "command": "list",
                    "data": {
                        "outstanding": outstanding,
                        "outstanding_order_count": total_count,
                    },
                }
            except DatabaseError:
                _logger.exception("Database error during list")
                return self._error_response(
                    "list",
                    ValidationError(DATABASE_ERROR, "Database error."),
                )
            except Exception:
                _logger.exception("Unhandled error during list")
                return self._error_response(
                    "list",
                    ValidationError(INTERNAL_ERROR, "Internal error."),
                )

    def fulfill_order(self, order_id: str, auth_code: str) -> Dict[str, object]:
        """Fulfill an order by ID."""

        with TimingContext(self._metrics, "total_ms"):
            try:
                canonical_id = validate_order_id(order_id)
                validate_auth_code_format(auth_code)
                if not self._auth_service.check(auth_code):
                    raise ValidationError(
                        UNAUTHORIZED,
                        "Unauthorized to fulfill order.",
                    )
                fulfilled_at = self._clock.now_utc_iso()
                order = self._repository.fulfill_order(canonical_id, fulfilled_at)
                self._metrics.orders_fulfilled_total += 1
                return {
                    "ok": True,
                    "command": "fulfill",
                    "data": {
                        "order_id": order.order_id,
                        "status": order.status.value,
                        "fulfilled_at_utc": order.fulfilled_at_utc,
                        "mobile": order.mobile,
                        "total_pence": order.total_pence,
                    },
                }
            except ValidationError as exc:
                return self._error_response("fulfill", exc)
            except OrderNotFoundError:
                return self._error_response(
                    "fulfill",
                    ValidationError(ORDER_NOT_FOUND, "Order not found."),
                )
            except OrderAlreadyFulfilledError:
                return self._error_response(
                    "fulfill",
                    ValidationError(
                        ORDER_ALREADY_FULFILLED,
                        "Order already fulfilled.",
                    ),
                )
            except DatabaseError:
                _logger.exception("Database error during fulfill")
                return self._error_response(
                    "fulfill",
                    ValidationError(DATABASE_ERROR, "Database error."),
                )
            except Exception:
                _logger.exception("Unhandled error during fulfill")
                return self._error_response(
                    "fulfill",
                    ValidationError(INTERNAL_ERROR, "Internal error."),
                )

    def show_order(self, order_id: str) -> Dict[str, object]:
        """Show a single order by ID."""

        with TimingContext(self._metrics, "total_ms"):
            try:
                canonical_id = validate_order_id(order_id)
                order = self._repository.get_order(canonical_id)
                if order is None:
                    raise ValidationError(ORDER_NOT_FOUND, "Order not found.")
                return {
                    "ok": True,
                    "command": "show",
                    "data": _order_payload(order, include_status=True, include_fulfilled=True),
                }
            except ValidationError as exc:
                return self._error_response("show", exc)
            except DatabaseError:
                _logger.exception("Database error during show")
                return self._error_response(
                    "show",
                    ValidationError(DATABASE_ERROR, "Database error."),
                )
            except Exception:
                _logger.exception("Unhandled error during show")
                return self._error_response(
                    "show",
                    ValidationError(INTERNAL_ERROR, "Internal error."),
                )

    def _build_order_lines(self, sku_quantities: Dict[str, int]) -> List[OrderLine]:
        """Build sorted order line items from SKU quantities."""

        items = []
        for sku, qty in sku_quantities.items():
            item = self._catalogue.get(sku)
            if item is None:
                continue
            total = qty * item.unit_price_pence
            items.append(
                OrderLine(
                    sku=item.sku,
                    qty=qty,
                    unit_price_pence=item.unit_price_pence,
                    line_total_pence=total,
                )
            )
        items.sort(key=lambda line: line.sku)
        return items

    def _build_order(self, mobile: str, message: str, items: List[OrderLine]) -> Order:
        """Build an Order object from validated inputs."""

        total = sum(line.line_total_pence for line in items)
        return Order(
            order_id=self._id_generator.new_order_id(),
            mobile=mobile,
            raw_message=message,
            items=items,
            status=OrderStatus.PENDING,
            created_at_utc=self._clock.now_utc_iso(),
            fulfilled_at_utc=None,
            total_pence=total,
        )

    def _create_order_with_retry(self, order: Order) -> Order:
        """Create an order with retry on ID collision."""

        last_error: Exception | None = None
        for _ in range(5):
            try:
                self._repository.create_order(order)
                return order
            except OrderAlreadyExistsError as exc:
                last_error = exc
                order = Order(
                    order_id=self._id_generator.new_order_id(),
                    mobile=order.mobile,
                    raw_message=order.raw_message,
                    items=order.items,
                    status=order.status,
                    created_at_utc=order.created_at_utc,
                    fulfilled_at_utc=order.fulfilled_at_utc,
                    total_pence=order.total_pence,
                )
        raise OrderAlreadyExistsError("Failed to generate unique order ID.") from last_error

    def _ensure_order_invariants(self, order: Order) -> None:
        """Check internal consistency invariants for constructed orders.

        These checks strengthen test oracles by turning internal inconsistencies
        into observable INTERNAL_ERROR outcomes.
        """
        if order.status != OrderStatus.PENDING:
            raise ValidationError(
                INTERNAL_ERROR,
                "Invariant violated: placed order must be PENDING.",
                details={"status": order.status.value},
            )
        computed_total = sum(line.line_total_pence for line in order.items)
        if computed_total != order.total_pence:
            raise ValidationError(
                INTERNAL_ERROR,
                "Invariant violated: total_pence mismatch.",
                details={"computed_total": computed_total, "total_pence": order.total_pence},
            )
        for line in order.items:
            if line.qty < 1:
                raise ValidationError(
                    INTERNAL_ERROR,
                    "Invariant violated: qty must be positive.",
                    details={"sku": line.sku, "qty": line.qty},
                )
            expected_line_total = line.qty * line.unit_price_pence
            if expected_line_total != line.line_total_pence:
                raise ValidationError(
                    INTERNAL_ERROR,
                    "Invariant violated: line_total mismatch.",
                    details={"sku": line.sku, "expected": expected_line_total, "actual": line.line_total_pence},
                )


    def _error_response(self, command: str, exc: ValidationError) -> Dict[str, object]:
        """Build a standard error response and update metrics."""

        self._metrics.orders_rejected_total += 1
        self._metrics.increment_error(exc.code)
        self._diagnostics.record("error", {"command": command, "code": exc.code, "message": exc.message, "details": exc.details or {}})
        error_payload: Dict[str, object] = {
            "code": exc.code,
            "message": exc.message,
        }
        if exc.details:
            error_payload["details"] = exc.details
        _logger.error(
            "OrderFlow error: %s %s %s",
            exc.code,
            exc.message,
            exc.details,
        )
        return {
            "ok": False,
            "command": command,
            "error": error_payload,
        }


def _order_payload(
    order: Order, *, include_status: bool = True, include_fulfilled: bool = False
) -> Dict[str, object]:
    """Build the standard order payload used by place/show."""

    payload: Dict[str, object] = {
        "order_id": order.order_id,
        "mobile": order.mobile,
        "status": order.status.value,
        "created_at_utc": order.created_at_utc,
        "total_pence": order.total_pence,
        "items": [
            {
                "sku": line.sku,
                "qty": line.qty,
                "unit_price_pence": line.unit_price_pence,
                "line_total_pence": line.line_total_pence,
            }
            for line in order.items
        ],
    }
    if include_fulfilled:
        payload["fulfilled_at_utc"] = order.fulfilled_at_utc
    if not include_status:
        payload.pop("status", None)
    return payload
