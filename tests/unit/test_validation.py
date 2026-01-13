"""Unit tests for validation helpers."""

from __future__ import annotations

import pytest

from orderflow.validation import (
    INVALID_MOBILE,
    MESSAGE_TOO_LONG,
    ValidationError,
    validate_auth_code_format,
    validate_message_length,
    validate_mobile,
    validate_order_id,
)


def test_T_UNIT_VALID_001_validations_accept_valid_inputs() -> None:
    """T-UNIT-VALID-001: validation helpers accept valid inputs."""

    assert validate_mobile(" +15551234567 ") == "+15551234567"
    validate_message_length("ORDER COFFEE=1")
    assert validate_order_id(" ORD-0000ABCD ") == "ORD-0000ABCD"
    assert validate_auth_code_format("123456") == "123456"


def test_T_UNIT_VALID_002_mobile_boundaries() -> None:
    """T-UNIT-VALID-002: mobile validation boundary cases."""

    for value in ["15551234567", "+1234", "+12345678901234567", "+12345ABCD"]:
        with pytest.raises(ValidationError) as excinfo:
            validate_mobile(value)
        assert excinfo.value.code == INVALID_MOBILE


def test_T_UNIT_VALID_003_message_length_boundaries() -> None:
    """T-UNIT-VALID-003: message length boundary cases."""

    valid_message = "A" * 256
    validate_message_length(valid_message)

    invalid_message = "B" * 257
    with pytest.raises(ValidationError) as excinfo:
        validate_message_length(invalid_message)
    assert excinfo.value.code == MESSAGE_TOO_LONG
