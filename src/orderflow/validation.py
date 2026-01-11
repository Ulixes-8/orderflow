"""Validation helpers for OrderFlow inputs."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Dict

INVALID_MOBILE = "INVALID_MOBILE"
MESSAGE_TOO_LONG = "MESSAGE_TOO_LONG"
PARSE_ERROR = "PARSE_ERROR"
TOO_MANY_ITEMS = "TOO_MANY_ITEMS"
UNKNOWN_ITEM = "UNKNOWN_ITEM"
INVALID_QUANTITY = "INVALID_QUANTITY"
ORDER_NOT_FOUND = "ORDER_NOT_FOUND"
ORDER_ALREADY_FULFILLED = "ORDER_ALREADY_FULFILLED"
UNAUTHORIZED = "UNAUTHORIZED"
INTERNAL_ERROR = "INTERNAL_ERROR"
DATABASE_ERROR = "DATABASE_ERROR"

_MOBILE_PATTERN = re.compile(r"^\+[1-9]\d{7,14}$")
_ORDER_ID_PATTERN = re.compile(r"^ORD-[0-9A-F]{8}$")
_AUTH_CODE_PATTERN = re.compile(r"^\d{6}$")


@dataclass
class ValidationError(Exception):
    """Error raised when validation fails for user input."""

    code: str
    message: str
    details: Dict[str, object] | None = None

    def __str__(self) -> str:
        """Return a string representation of the validation error."""

        return f"{self.code}: {self.message}"


def validate_mobile(mobile: str) -> str:
    """Validate an E.164 mobile number and return the canonical value."""

    mobile = mobile.strip()
    if not _MOBILE_PATTERN.fullmatch(mobile):
        raise ValidationError(INVALID_MOBILE, "Invalid mobile number format.")
    return mobile


def validate_message_length(message: str, max_len: int = 256) -> None:
    """Validate the message length after trimming the trailing newline."""

    normalized = message.rstrip("\n")
    if len(normalized) > max_len:
        raise ValidationError(
            MESSAGE_TOO_LONG,
            f"Message exceeds maximum length of {max_len} characters.",
            details={"max_len": max_len},
        )


def validate_order_id(order_id: str) -> str:
    """Validate the order ID format."""

    order_id = order_id.strip()
    if not _ORDER_ID_PATTERN.fullmatch(order_id):
        raise ValidationError(
            PARSE_ERROR,
            "Invalid order ID format.",
            details={"field": "order_id"},
        )
    return order_id


def validate_auth_code_format(code: str) -> str:
    """Validate the auth code format."""

    code = code.strip()
    if not _AUTH_CODE_PATTERN.fullmatch(code):
        raise ValidationError(
            PARSE_ERROR,
            "Invalid auth code format.",
            details={"field": "auth_code"},
        )
    return code
