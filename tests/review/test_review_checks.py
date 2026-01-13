"""Static review tests for architecture and security evidence."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from typing import Protocol

import pytest

from orderflow.service import OrderService
from orderflow.store import base as store_base


@pytest.mark.review
def test_T_REVIEW_SEC_001_sql_uses_parameters() -> None:
    """T-REVIEW-SEC-001: ensure SQL uses parameter substitution."""

    sqlite_path = Path("src/orderflow/store/sqlite.py")
    source = sqlite_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in {"execute", "executemany"}:
            continue
        if not node.args:
            continue
        sql_node = node.args[0]
        if isinstance(sql_node, ast.JoinedStr):
            pytest.fail("Found f-string SQL; parameters must be bound.")


@pytest.mark.review
def test_T_REVIEW_ARCH_001_testability_seams_exist() -> None:
    """T-REVIEW-ARCH-001: architecture supports dependency injection."""

    signature = inspect.signature(OrderService.__init__)
    params = signature.parameters
    assert "repository" in params
    assert "clock" in params
    assert "id_generator" in params

    assert issubclass(store_base.OrderRepository, Protocol)
