#!/usr/bin/env python3
"""
Validate LO1 artefacts for OrderFlow.

Purpose:
- Improve process visibility (early detection of specification inconsistencies).
- Provide a lightweight static check on the LO1 "test basis" and traceability.

Checks:
- requirements.json is well-formed and contains unique requirement IDs.
- each requirement has required fields and uses allowed enums.
- traceability.csv references only known requirement IDs.
- planned_test_ids is non-empty for every traceability row.

This is intentionally small and dependency-free (stdlib only).
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


_ALLOWED_TYPES = {
    "functional_correctness",
    "safety",
    "liveness",
    "robustness",
    "security",
    "performance",
    "qualitative",
}
_ALLOWED_LEVELS = {"system", "integration", "unit"}
_ALLOWED_PRIORITIES = {"P0", "P1", "P2"}


@dataclass(frozen=True)
class ValidationIssue:
    """A single validation issue discovered during LO1 checks."""

    location: str
    message: str


def _load_json(path: Path) -> Any:
    """Load JSON from a file, raising a readable error on failure."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to read JSON: {path}: {exc}") from exc


def _validate_requirements(data: Any) -> tuple[set[str], list[ValidationIssue]]:
    """Validate the requirements JSON structure and contents."""
    issues: list[ValidationIssue] = []

    if not isinstance(data, dict):
        return set(), [ValidationIssue("requirements.json", "Top-level must be an object")]

    reqs = data.get("requirements")
    if not isinstance(reqs, list):
        return set(), [ValidationIssue("requirements.json", "`requirements` must be a list")]

    ids: set[str] = set()
    for idx, req in enumerate(reqs):
        loc = f"requirements.json:requirements[{idx}]"
        if not isinstance(req, dict):
            issues.append(ValidationIssue(loc, "Requirement must be an object"))
            continue

        rid = req.get("id")
        rtype = req.get("type")
        level = req.get("level")
        priority = req.get("priority")
        verifiable = req.get("verifiable")
        statement = req.get("statement")
        acceptance = req.get("acceptance")
        stakeholder = req.get("stakeholder")

        if not isinstance(rid, str) or not rid.strip():
            issues.append(ValidationIssue(loc, "Missing/invalid `id`"))
        else:
            if rid in ids:
                issues.append(ValidationIssue(loc, f"Duplicate requirement id: {rid}"))
            ids.add(rid)

        if rtype not in _ALLOWED_TYPES:
            issues.append(ValidationIssue(loc, f"Invalid `type`: {rtype!r}"))
        if level not in _ALLOWED_LEVELS:
            issues.append(ValidationIssue(loc, f"Invalid `level`: {level!r}"))
        if priority not in _ALLOWED_PRIORITIES:
            issues.append(ValidationIssue(loc, f"Invalid `priority`: {priority!r}"))
        if not isinstance(verifiable, bool):
            issues.append(ValidationIssue(loc, "`verifiable` must be boolean"))
        if not isinstance(statement, str) or not statement.strip():
            issues.append(ValidationIssue(loc, "Missing/invalid `statement`"))
        if not isinstance(acceptance, str) or not acceptance.strip():
            issues.append(ValidationIssue(loc, "Missing/invalid `acceptance`"))
        if not isinstance(stakeholder, str) or not stakeholder.strip():
            issues.append(ValidationIssue(loc, "Missing/invalid `stakeholder`"))

    return ids, issues


def _read_traceability(path: Path) -> Iterable[dict[str, str]]:
    """Read traceability CSV rows as dictionaries."""
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield {k: (v or "").strip() for k, v in row.items()}


def _validate_traceability(
    req_ids: set[str], rows: Iterable[dict[str, str]]
) -> list[ValidationIssue]:
    """Validate traceability entries reference known requirement IDs."""
    issues: list[ValidationIssue] = []
    for i, row in enumerate(rows, start=2):  # header is line 1
        loc = f"traceability.csv:line {i}"
        rid = row.get("requirement_id", "")
        planned = row.get("planned_test_ids", "")

        if not rid:
            issues.append(ValidationIssue(loc, "Missing requirement_id"))
            continue
        if rid not in req_ids:
            issues.append(ValidationIssue(loc, f"Unknown requirement_id: {rid}"))

        if not planned:
            issues.append(ValidationIssue(loc, "planned_test_ids must be non-empty"))

    return issues


def main() -> int:
    """Entry point for LO1 artefact validation."""
    parser = argparse.ArgumentParser(description="Validate LO1 artefacts.")
    parser.add_argument(
        "--requirements",
        type=Path,
        default=Path("docs/lo1/requirements.json"),
        help="Path to requirements.json",
    )
    parser.add_argument(
        "--traceability",
        type=Path,
        default=Path("docs/lo1/traceability.csv"),
        help="Path to traceability.csv",
    )
    args = parser.parse_args()

    issues: list[ValidationIssue] = []

    req_data = _load_json(args.requirements)
    req_ids, req_issues = _validate_requirements(req_data)
    issues.extend(req_issues)

    if args.traceability.exists():
        issues.extend(_validate_traceability(req_ids, _read_traceability(args.traceability)))
    else:
        issues.append(ValidationIssue(str(args.traceability), "Traceability file not found"))

    if issues:
        print("LO1 validation FAILED:")
        for issue in issues:
            print(f"- {issue.location}: {issue.message}")
        return 1

    print("LO1 validation PASSED.")
    print(f"- Requirements: {len(req_ids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
