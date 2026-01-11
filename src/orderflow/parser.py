"""Parsing helpers for OrderFlow messages."""

from __future__ import annotations

import re
from typing import Dict

from orderflow.validation import INVALID_QUANTITY, PARSE_ERROR, TOO_MANY_ITEMS, ValidationError

_SKU_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,31}$")


def parse_order_message(
    message: str, max_items: int = 20, max_qty: int = 99
) -> Dict[str, int]:
    """Parse a place-order message into aggregated SKU quantities."""

    stripped = message.lstrip()
    if not stripped:
        raise ValidationError(PARSE_ERROR, "Empty message.", details={"token": ""})

    tokens = stripped.split()
    if not tokens or tokens[0].upper() != "ORDER":
        raise ValidationError(PARSE_ERROR, "Message must start with ORDER.")

    item_tokens = tokens[1:]
    if not item_tokens:
        raise ValidationError(PARSE_ERROR, "Message must include at least one item.")

    if len(item_tokens) > max_items:
        raise ValidationError(
            TOO_MANY_ITEMS,
            f"Message contains more than {max_items} items.",
            details={"max_items": max_items},
        )

    aggregated: Dict[str, int] = {}
    for token in item_tokens:
        sku_part, qty_part = _split_token(token)
        if not _SKU_PATTERN.fullmatch(sku_part):
            raise ValidationError(
                PARSE_ERROR,
                "Invalid SKU token.",
                details={"token": token},
            )
        qty = _parse_qty(qty_part, max_qty, token)
        sku = sku_part.upper()
        aggregated[sku] = aggregated.get(sku, 0) + qty
        if aggregated[sku] > max_qty:
            raise ValidationError(
                INVALID_QUANTITY,
                "Aggregated quantity exceeds allowed maximum.",
                details={"token": token},
            )
    return aggregated


def _split_token(token: str) -> tuple[str, str | None]:
    """Split SKU or SKU=QTY tokens."""

    if "=" not in token:
        return token, None
    parts = token.split("=", 1)
    return parts[0], parts[1]


def _parse_qty(qty_part: str | None, max_qty: int, token: str) -> int:
    """Parse a quantity component for a token."""

    if qty_part is None:
        return 1
    if not qty_part.isdigit():
        raise ValidationError(
            INVALID_QUANTITY,
            "Quantity must be numeric.",
            details={"token": token},
        )
    qty = int(qty_part)
    if qty < 1 or qty > max_qty:
        raise ValidationError(
            INVALID_QUANTITY,
            "Quantity is out of allowed range.",
            details={"token": token},
        )
    return qty
