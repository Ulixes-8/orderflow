"""Unit tests for message parsing."""

from __future__ import annotations

import pytest

from orderflow.parser import parse_order_message
from orderflow.validation import (
    INVALID_QUANTITY,
    PARSE_ERROR,
    TOO_MANY_ITEMS,
    ValidationError,
)


def test_T_UNIT_PARSER_001_accepts_valid_partitions() -> None:
    """T-UNIT-PARSER-001: parser accepts valid representative partitions."""

    message = "ORDER coffee=2 TEA sandwich"
    parsed = parse_order_message(message)
    assert parsed == {"COFFEE": 2, "TEA": 1, "SANDWICH": 1}


def test_T_UNIT_PARSER_002_rejects_invalid_syntax() -> None:
    """T-UNIT-PARSER-002: parser rejects grammar violations."""

    with pytest.raises(ValidationError) as excinfo:
        parse_order_message("BUY COFFEE=1")
    assert excinfo.value.code == PARSE_ERROR

    with pytest.raises(ValidationError) as excinfo:
        parse_order_message("ORDER")
    assert excinfo.value.code == PARSE_ERROR

    with pytest.raises(ValidationError) as excinfo:
        parse_order_message("ORDER COFFEE=abc")
    assert excinfo.value.code == INVALID_QUANTITY


def test_T_UNIT_PARSER_003_enforces_boundaries() -> None:
    """T-UNIT-PARSER-003: parser enforces max items and qty boundaries."""

    too_many_items = "ORDER " + " ".join(["COFFEE=1"] * 21)
    with pytest.raises(ValidationError) as excinfo:
        parse_order_message(too_many_items)
    assert excinfo.value.code == TOO_MANY_ITEMS

    with pytest.raises(ValidationError) as excinfo:
        parse_order_message("ORDER COFFEE=100")
    assert excinfo.value.code == INVALID_QUANTITY

    with pytest.raises(ValidationError) as excinfo:
        parse_order_message("ORDER COFFEE=60 COFFEE=60")
    assert excinfo.value.code == INVALID_QUANTITY
