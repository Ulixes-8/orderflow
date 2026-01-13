#!/usr/bin/env python3
"""LO3: Extract planned-vs-implemented status.

This script compares planned tests from the LO2 inventory against
implemented pytest tests and their execution status from junit.xml.
"""

from __future__ import annotations

import argparse
import ast
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class Args:
    """Command line arguments."""

    inventory: Path
    junit_xml: Path
    out: Path


@dataclass(frozen=True)
class TestLocation:
    """Location metadata for an implemented test."""

    file: str
    function: str


@dataclass(frozen=True)
class InventoryRow:
    """Representation of a planned test row from the inventory."""

    test_id: str
    level: str
    primary_technique: str
    linked_requirements: list[str]


@dataclass(frozen=True)
class TestCaseResult:
    """JUnit testcase execution status."""

    name: str
    status: str


def parse_args() -> Args:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description="Extract LO3 plan status.")
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--junit-xml", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    ns = parser.parse_args()
    return Args(inventory=ns.inventory, junit_xml=ns.junit_xml, out=ns.out)


def _read_inventory(path: Path) -> list[InventoryRow]:
    """Read LO2 inventory entries."""

    rows: list[InventoryRow] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            test_id = (row.get("test_id") or "").strip()
            if not test_id:
                continue
            linked = [item.strip() for item in (row.get("linked_requirements") or "").split(";") if item.strip()]
            rows.append(
                InventoryRow(
                    test_id=test_id,
                    level=(row.get("level") or "").strip(),
                    primary_technique=(row.get("primary_technique") or "").strip(),
                    linked_requirements=linked,
                )
            )
    return rows


def _iter_python_files(root: Path) -> Iterable[Path]:
    """Yield Python files under a root directory."""

    for path in root.rglob("*.py"):
        if path.is_file():
            yield path


def _normalize_test_id(test_id: str) -> str:
    """Normalize a test ID for function-name matching."""

    return test_id.replace("-", "_")


def _collect_test_locations(root: Path) -> dict[str, list[TestLocation]]:
    """Collect implemented pytest test functions keyed by function name."""

    mapping: dict[str, list[TestLocation]] = {}
    for path in _iter_python_files(root):
        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            continue
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = node.name
                if "test_T_" not in name:
                    continue
                mapping.setdefault(name, []).append(
                    TestLocation(file=str(path), function=name)
                )
    return mapping


def _find_locations_for_test_id(
    test_id: str, test_locations: dict[str, list[TestLocation]]
) -> list[TestLocation]:
    """Find locations for a planned test id by substring match."""

    normalized = _normalize_test_id(test_id)
    matches: list[TestLocation] = []
    for locations in test_locations.values():
        for location in locations:
            if test_id in location.function or normalized in location.function:
                matches.append(location)
    return matches


def _parse_junit(path: Path) -> list[TestCaseResult]:
    """Parse pytest JUnit XML into testcase results."""

    tree = ET.parse(path)
    root = tree.getroot()
    results: list[TestCaseResult] = []
    for testcase in root.iter("testcase"):
        name = testcase.get("name", "")
        status = "PASS"
        failure = testcase.find("failure")
        skipped = testcase.find("skipped")
        if failure is not None:
            status = "FAIL"
        elif skipped is not None:
            message = (skipped.get("message") or "").lower()
            if "xfail" in message:
                status = "XFAIL"
            else:
                status = "SKIP"
        results.append(TestCaseResult(name=name, status=status))
    return results


def _matching_results(test_id: str, results: list[TestCaseResult]) -> list[TestCaseResult]:
    """Return results matching a planned test id."""

    normalized = _normalize_test_id(test_id)
    return [
        result
        for result in results
        if test_id in result.name or normalized in result.name
    ]


def _status_from_results(results: list[TestCaseResult]) -> str:
    """Determine aggregate status from testcase results."""

    statuses = {result.status for result in results}
    if "FAIL" in statuses:
        return "FAIL"
    if "PASS" in statuses:
        return "PASS"
    if "XFAIL" in statuses:
        return "XFAIL"
    if "SKIP" in statuses:
        return "SKIP"
    return "DEFERRED"


def main() -> int:
    """Main entry point."""

    args = parse_args()
    inventory_rows = _read_inventory(args.inventory)
    test_locations = _collect_test_locations(Path("tests"))
    junit_results = _parse_junit(args.junit_xml)

    tests_payload: list[dict[str, object]] = []
    summary = {
        "planned_total": len(inventory_rows),
        "implemented_total": 0,
        "pass": 0,
        "fail": 0,
        "skip": 0,
        "xfail": 0,
        "deferred": 0,
    }

    for row in sorted(inventory_rows, key=lambda r: r.test_id):
        locations = _find_locations_for_test_id(row.test_id, test_locations)
        results = _matching_results(row.test_id, junit_results)
        implemented = bool(locations)
        notes = ""
        if not implemented:
            status = "DEFERRED"
            notes = "No test found with required ID pattern."
        else:
            status = _status_from_results(results)
            if status == "DEFERRED":
                notes = "No matching JUnit results found for implemented tests."
        if implemented:
            summary["implemented_total"] += 1
        if status == "PASS":
            summary["pass"] += 1
        elif status == "FAIL":
            summary["fail"] += 1
        elif status == "SKIP":
            summary["skip"] += 1
        elif status == "XFAIL":
            summary["xfail"] += 1
        elif status == "DEFERRED":
            summary["deferred"] += 1

        tests_payload.append(
            {
                "test_id": row.test_id,
                "level": row.level,
                "primary_technique": row.primary_technique,
                "linked_requirements": row.linked_requirements,
                "implemented": implemented,
                "status": status,
                "locations": [
                    {"file": loc.file, "function": loc.function}
                    for loc in locations
                ],
                "notes": notes,
            }
        )

    payload = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "inventory_path": str(args.inventory),
        "summary": summary,
        "tests": tests_payload,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json_dumps(payload),
        encoding="utf-8",
    )
    return 0


def json_dumps(payload: dict[str, object]) -> str:
    """Serialize JSON with deterministic formatting."""

    import json

    return json.dumps(payload, sort_keys=True, indent=2)


if __name__ == "__main__":
    raise SystemExit(main())
