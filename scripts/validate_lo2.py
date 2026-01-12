#!/usr/bin/env python3
"""Validate LO2 artefacts exist and are internally consistent.

This is intentionally lightweight: it checks that key LO2 documents exist and
that the test plan references the LO1 test basis artefacts.
"""

from __future__ import annotations

from pathlib import Path
import sys


REQUIRED_FILES = [
    Path("docs/lo2/test_plan.md"),
    Path("docs/lo2/test_inventory.csv"),
    Path("docs/lo2/plan_evolution.md"),
    Path("docs/lo2/plan_review.md"),
    Path("docs/lo2/instrumentation.md"),
    Path("docs/lo2/instrumentation_review.md"),
]


def main() -> int:
    missing = [str(p) for p in REQUIRED_FILES if not p.exists()]
    if missing:
        print("LO2 validation FAILED: missing files:")
        for p in missing:
            print(f"- {p}")
        return 1

    plan = Path("docs/lo2/test_plan.md").read_text(encoding="utf-8")
    required_refs = [
        "docs/lo1/requirements.json",
        "docs/lo1/test-approach.md",
        "docs/lo1/traceability.csv",
    ]
    for ref in required_refs:
        if ref not in plan:
            print(f"LO2 validation FAILED: test_plan.md missing reference: {ref}")
            return 1

    print("LO2 validation PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
