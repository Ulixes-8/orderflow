#!/usr/bin/env python3
"""Validate LO2 artefacts exist and are internally consistent with LO1.

Checks:
- Required LO2 files exist.
- test_plan.md references the LO1 test basis artefacts.
- Every planned test ID in LO1 traceability.csv appears in LO2 test_inventory.csv.
- Every LO1 requirement ID appears in at least one LO2 inventory row (planned coverage).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
import sys


REQUIRED_FILES = [
    Path("docs/lo2/test_plan.md"),
    Path("docs/lo2/test_inventory.csv"),
    Path("docs/lo2/plan_evolution.md"),
    Path("docs/lo2/plan_review.md"),
    Path("docs/lo2/instrumentation.md"),
    Path("docs/lo2/instrumentation_review.md"),
    # Contract basis for system tests (expected by plan)
    Path("docs/cli_contract.md"),
]

LO1_REFS = [
    "docs/lo1/requirements.json",
    "docs/lo1/test-approach.md",
    "docs/lo1/traceability.csv",
]


def _normalize_csv_value(value: object) -> str:
    """Normalize CSV values to a safe, stripped string representation."""

    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple)):
        return " ".join(
            str(item).strip() for item in value if str(item).strip()
        ).strip()
    return str(value).strip()


def _read_csv(path: Path) -> list[dict[str, str]]:
    """Read a CSV file into a list of sanitized dictionaries."""

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [{k: _normalize_csv_value(v) for k, v in row.items()} for row in reader]


def _load_requirements(path: Path) -> set[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    reqs = data.get("requirements", [])
    return {r.get("id", "").strip() for r in reqs if isinstance(r, dict) and r.get("id")}


def main() -> int:
    missing = [str(p) for p in REQUIRED_FILES if not p.exists()]
    if missing:
        print("LO2 validation FAILED: missing files:")
        for p in missing:
            print(f"- {p}")
        return 1

    plan_text = Path("docs/lo2/test_plan.md").read_text(encoding="utf-8")
    for ref in LO1_REFS:
        if ref not in plan_text:
            print(f"LO2 validation FAILED: test_plan.md missing reference: {ref}")
            return 1

    # Load LO1 planned test IDs
    trace_rows = _read_csv(Path("docs/lo1/traceability.csv"))
    planned_ids: set[str] = set()
    for row in trace_rows:
        for tid in (row.get("planned_test_ids", "") or "").split(";"):
            tid = tid.strip()
            if tid:
                planned_ids.add(tid)

    # Load LO2 inventory test IDs and linked requirements
    inv_rows = _read_csv(Path("docs/lo2/test_inventory.csv"))
    inventory_ids = {row.get("test_id", "") for row in inv_rows if row.get("test_id")}
    inventory_req_ids: set[str] = set()
    for row in inv_rows:
        linked = row.get("linked_requirements", "") or ""
        for rid in linked.split(";"):
            rid = rid.strip()
            if rid:
                inventory_req_ids.add(rid)

    # Check: every LO1 planned test ID is present in LO2 inventory
    missing_test_ids = sorted(planned_ids - inventory_ids)
    if missing_test_ids:
        print("LO2 validation FAILED: LO1 traceability test IDs missing from LO2 inventory:")
        for tid in missing_test_ids:
            print(f"- {tid}")
        return 1

    # Check: every LO1 requirement appears in inventory (planned coverage)
    lo1_req_ids = _load_requirements(Path("docs/lo1/requirements.json"))
    uncovered_req_ids = sorted(r for r in lo1_req_ids if r and r not in inventory_req_ids)
    if uncovered_req_ids:
        print("LO2 validation FAILED: LO1 requirements missing from LO2 inventory linked_requirements:")
        for rid in uncovered_req_ids:
            print(f"- {rid}")
        return 1

    print("LO2 validation PASSED.")
    print(f"- Inventory tests: {len(inventory_ids)}")
    print(f"- LO1 planned tests covered: {len(planned_ids)}")
    print(f"- LO1 requirements covered: {len(lo1_req_ids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
