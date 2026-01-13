"""Property-based tests for parser behavior."""

from __future__ import annotations

import pytest

hypothesis = pytest.importorskip("hypothesis", reason="Hypothesis not installed.")
given = hypothesis.given
settings = hypothesis.settings
st = hypothesis.strategies

from orderflow.parser import parse_order_message


SKUS = ["COFFEE", "TEA", "SANDWICH", "CAKE", "JUICE", "WATER"]


@pytest.mark.property
@settings(max_examples=100, derandomize=True, deadline=None)
@given(
    st.lists(
        st.tuples(st.sampled_from(SKUS), st.integers(min_value=1, max_value=5)),
        min_size=1,
        max_size=5,
    )
)
def test_T_UNIT_PARSER_001_valid_messages_are_parsed(items: list[tuple[str, int]]) -> None:
    """T-UNIT-PARSER-001: valid messages parse into aggregated quantities."""

    parts = [f"{sku}={qty}" for sku, qty in items]
    message = "ORDER " + " ".join(parts)
    parsed = parse_order_message(message)
    assert all(qty >= 1 for qty in parsed.values())
    assert all(sku in SKUS for sku in parsed)
