"""Command-line interface for OrderFlow."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Iterable, Tuple

from orderflow.auth import AuthService
from orderflow.catalogue import Catalogue
from orderflow.metrics import MetricsCollector, MetricsStore
from orderflow.service import OrderService, RandomIdGenerator, ServiceLimits, SystemClock
from orderflow.store.sqlite import SQLiteOrderRepository
from orderflow.validation import (
    DATABASE_ERROR,
    INTERNAL_ERROR,
    INVALID_MOBILE,
    INVALID_QUANTITY,
    MESSAGE_TOO_LONG,
    ORDER_ALREADY_FULFILLED,
    ORDER_NOT_FOUND,
    PARSE_ERROR,
    TOO_MANY_ITEMS,
    UNAUTHORIZED,
    UNKNOWN_ITEM,
)

_LOGGER = logging.getLogger(__name__)

_COMMANDS = {"place", "list", "fulfill", "show", "batch", "metrics"}

_VALIDATION_CODES = {
    INVALID_MOBILE,
    MESSAGE_TOO_LONG,
    PARSE_ERROR,
    TOO_MANY_ITEMS,
    UNKNOWN_ITEM,
    INVALID_QUANTITY,
}


def main() -> None:
    """Entry point for the OrderFlow CLI."""

    args = _parse_args(sys.argv[1:])
    _configure_logging(args.log_level)

    db_path = args.db or os.getenv("ORDERFLOW_DB_PATH", "./orderflow.db")
    required_auth_code = args.auth_code or os.getenv("ORDERFLOW_AUTH_CODE", "123456")

    _LOGGER.info("OrderFlow command invoked: %s", args.command)
    _LOGGER.info("Using database path: %s", db_path)

    repository = SQLiteOrderRepository(db_path)
    repository.init_schema()
    catalogue = Catalogue.load(args.catalog)
    auth_service = AuthService(required_auth_code)
    metrics_store = MetricsStore(db_path)
    metrics_store.init_schema()
    metrics = metrics_store.load()
    service = OrderService(
        repository=repository,
        catalogue=catalogue,
        auth_service=auth_service,
        clock=SystemClock(),
        id_generator=RandomIdGenerator(),
        metrics=metrics,
        limits=ServiceLimits(),
    )

    if args.command == "place":
        response = service.place_order(args.mobile, args.message)
        _print_json(response)
        metrics_store.save(metrics)
        sys.exit(_exit_code_for_response(response))
    if args.command == "list":
        response = service.list_outstanding()
        if response.get("ok") and args.format == "lines":
            _print_list_lines(response)
            metrics_store.save(metrics)
            sys.exit(0)
        _print_json(response)
        metrics_store.save(metrics)
        sys.exit(_exit_code_for_response(response))
    if args.command == "fulfill":
        response = service.fulfill_order(args.order_id, args.request_auth_code)
        _print_json(response)
        metrics_store.save(metrics)
        sys.exit(_exit_code_for_response(response))
    if args.command == "show":
        response = service.show_order(args.order_id)
        _print_json(response)
        metrics_store.save(metrics)
        sys.exit(_exit_code_for_response(response))
    if args.command == "batch":
        exit_code = _handle_batch(service, args.input)
        metrics_store.save(metrics)
        sys.exit(exit_code)
    if args.command == "metrics":
        response = _metrics_response(metrics)
        _print_json(response)
        if args.reset:
            metrics.reset()
        metrics_store.save(metrics)
        sys.exit(0)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments with support for list --format placement."""

    command_index = _find_command_index(argv)
    if command_index is None:
        parser = _build_full_parser()
        return parser.parse_args(argv)

    global_args = argv[:command_index]
    command = argv[command_index]
    command_args = argv[command_index + 1 :]

    global_parser = _build_global_parser()
    global_ns = global_parser.parse_args(global_args)
    command_parser = _build_command_parser(command)
    command_ns = command_parser.parse_args(command_args)
    merged = dict(vars(global_ns))
    merged.update(vars(command_ns))
    merged["command"] = command
    namespace = argparse.Namespace(**merged)
    _validate_format_usage(namespace)
    return namespace


def _build_full_parser() -> argparse.ArgumentParser:
    """Build the full parser used for help and fallback parsing."""

    parser = _build_global_parser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in sorted(_COMMANDS):
        subparsers.add_parser(name)
    return parser


def _build_global_parser() -> argparse.ArgumentParser:
    """Build the parser for global options."""

    parser = argparse.ArgumentParser(prog="orderflow")
    parser.add_argument("--db", help="Path to the SQLite database.")
    parser.add_argument("--catalog", help="Path to the catalogue JSON file.")
    parser.add_argument("--auth-code", help="Required authorization code.")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level.",
    )
    parser.add_argument(
        "--format",
        default="json",
        choices=["json", "lines"],
        help="Output format (list supports lines).",
    )
    return parser


def _build_command_parser(command: str) -> argparse.ArgumentParser:
    """Build the parser for command-specific options."""

    parser = argparse.ArgumentParser(prog=f"orderflow {command}")
    if command == "place":
        parser.add_argument("--mobile", required=True)
        parser.add_argument("--message", required=True)
        return parser
    if command == "list":
        parser.add_argument(
            "--format",
            default=argparse.SUPPRESS,
            choices=["json", "lines"],
            help="Output format for list.",
        )
        return parser
    if command == "fulfill":
        parser.add_argument("--order-id", required=True)
        parser.add_argument("--auth-code", dest="request_auth_code", required=True)
        return parser
    if command == "show":
        parser.add_argument("--order-id", required=True)
        return parser
    if command == "batch":
        parser.add_argument("--input", required=True)
        return parser
    if command == "metrics":
        parser.add_argument("--reset", action="store_true")
        return parser
    raise ValueError(f"Unknown command: {command}")


def _find_command_index(argv: list[str]) -> int | None:
    """Find the index of the subcommand in the argument list."""

    options_with_values = {"--db", "--catalog", "--auth-code", "--log-level", "--format"}
    skip_next = False
    for index, token in enumerate(argv):
        if skip_next:
            skip_next = False
            continue
        if token.startswith("--"):
            if token in options_with_values:
                skip_next = True
                continue
            if "=" in token:
                continue
        if token in _COMMANDS:
            return index
    return None


def _validate_format_usage(args: argparse.Namespace) -> None:
    """Validate --format usage for list and emit errors if invalid."""

    if args.command == "list":
        return
    if args.format != "json":
        _print_json(
            {
                "ok": False,
                "command": args.command,
                "error": {
                    "code": PARSE_ERROR,
                    "message": "Only list supports --format lines.",
                    "details": {"field": "format"},
                },
            }
        )
        sys.exit(2)


def _configure_logging(level: str) -> None:
    """Configure logging to stderr."""

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def _print_json(payload: dict) -> None:
    """Print a JSON payload deterministically to stdout."""

    sys.stdout.write(json.dumps(payload, sort_keys=True))
    sys.stdout.write("\n")


def _print_list_lines(response: dict) -> None:
    """Print the list command output in line format."""

    data = response.get("data", {})
    for mobile_entry in data.get("outstanding", []):
        mobile = mobile_entry.get("mobile")
        orders = mobile_entry.get("orders", [])
        order_parts = []
        for order in orders:
            items = order.get("items", [])
            item_parts = [f"{item['sku']}={item['qty']}" for item in items]
            order_parts.append(f"{order['order_id']}:{','.join(item_parts)}")
        line = f"{mobile} | {' ; '.join(order_parts)}"
        sys.stdout.write(f"{line}\n")


def _exit_code_for_response(response: dict) -> int:
    """Return the exit code corresponding to a response object."""

    if response.get("ok"):
        return 0
    error = response.get("error", {})
    code = error.get("code")
    if code in _VALIDATION_CODES:
        return 2
    if code == UNAUTHORIZED:
        return 3
    if code == ORDER_NOT_FOUND:
        return 4
    if code == ORDER_ALREADY_FULFILLED:
        return 5
    if code in {INTERNAL_ERROR, DATABASE_ERROR}:
        return 1
    return 1


def _metrics_response(metrics: MetricsCollector) -> dict:
    """Build the metrics response payload."""

    return {
        "ok": True,
        "command": "metrics",
        "data": {
            "counters": {
                "messages_processed_total": metrics.messages_processed_total,
                "orders_created_total": metrics.orders_created_total,
                "orders_rejected_total": metrics.orders_rejected_total,
                "orders_fulfilled_total": metrics.orders_fulfilled_total,
                "errors_total": metrics.errors_total,
                "errors_by_code": metrics.errors_by_code,
            },
            "timings": metrics.summary(),
        },
    }


def _handle_batch(service: OrderService, input_path: str) -> int:
    """Handle batch processing of input lines."""

    lines = _iter_batch_lines(input_path)
    processed = 0
    succeeded = 0
    failed = 0
    has_validation_error = False
    has_internal_error = False
    for line_no, mobile, message, is_valid in lines:
        processed += 1
        if is_valid:
            response = service.place_order(mobile, message)
        else:
            response = {
                "ok": False,
                "command": "place",
                "error": {
                    "code": PARSE_ERROR,
                    "message": "Invalid batch line format.",
                    "details": {"line_no": line_no},
                },
            }
        if response.get("ok"):
            succeeded += 1
        else:
            failed += 1
            error_code = response.get("error", {}).get("code")
            if error_code in _VALIDATION_CODES:
                has_validation_error = True
            elif error_code in {INTERNAL_ERROR, DATABASE_ERROR}:
                has_internal_error = True
            else:
                has_internal_error = True
        _print_json(
            {
                "line_no": line_no,
                "mobile": mobile,
                "message": message,
                "response": response,
            }
        )
    summary = {
        "ok": True,
        "command": "batch_summary",
        "data": {
            "lines_processed": processed,
            "lines_succeeded": succeeded,
            "lines_failed": failed,
        },
    }
    _print_json(summary)
    if has_internal_error:
        return 1
    if has_validation_error:
        return 2
    return 0


def _iter_batch_lines(input_path: str) -> Iterable[Tuple[int, str, str, bool]]:
    """Yield parsed batch lines as (line_no, mobile, message, is_valid)."""

    if input_path == "-":
        content = sys.stdin.read().splitlines()
    else:
        content = Path(input_path).read_text(encoding="utf-8").splitlines()

    for line_no, raw_line in enumerate(content, start=1):
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if "|" not in raw_line:
            yield line_no, raw_line, "", False
            continue
        mobile, message = raw_line.split("|", 1)
        yield line_no, mobile, message, True
