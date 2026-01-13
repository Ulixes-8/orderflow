#!/usr/bin/env python3
"""LO3: Compute coverage + yield metrics."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class Args:
    """Command line arguments."""

    requirements: Path
    traceability: Path
    inventory: Path
    coverage_xml: Path
    junit_xml: Path
    error_codes: Path
    performance: Path
    out: Path


@dataclass(frozen=True)
class TestCaseResult:
    """JUnit testcase execution status."""

    name: str
    status: str


def parse_args() -> Args:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description="Compute LO3 metrics.")
    parser.add_argument("--requirements", type=Path, required=True)
    parser.add_argument("--traceability", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--coverage-xml", type=Path, required=True)
    parser.add_argument("--junit-xml", type=Path, required=True)
    parser.add_argument("--error-codes", type=Path, required=True)
    parser.add_argument("--performance", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    ns = parser.parse_args()
    return Args(
        requirements=ns.requirements,
        traceability=ns.traceability,
        inventory=ns.inventory,
        coverage_xml=ns.coverage_xml,
        junit_xml=ns.junit_xml,
        error_codes=ns.error_codes,
        performance=ns.performance,
        out=ns.out,
    )


def _normalize_test_id(test_id: str) -> str:
    """Normalize a test id for name matching."""

    return test_id.replace("-", "_")


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


def _parse_requirements(path: Path) -> list[str]:
    """Read requirement IDs from LO1 requirements.json."""

    data = json.loads(path.read_text(encoding="utf-8"))
    reqs = data.get("requirements", [])
    ids: list[str] = []
    for req in reqs:
        if isinstance(req, dict):
            rid = req.get("id")
            if isinstance(rid, str) and rid.strip():
                ids.append(rid.strip())
    return ids


def _read_traceability(path: Path) -> list[dict[str, str]]:
    """Read traceability CSV rows as dictionaries."""

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [{k: (v or "").strip() for k, v in row.items()} for row in reader]


def _planned_tests_by_requirement(rows: Iterable[dict[str, str]]) -> dict[str, list[str]]:
    """Collect planned test IDs per requirement."""

    mapping: dict[str, list[str]] = {}
    for row in rows:
        requirement_id = (row.get("requirement_id") or "").strip()
        planned_ids = [
            item.strip()
            for item in (row.get("planned_test_ids") or "").split(";")
            if item.strip()
        ]
        if requirement_id:
            mapping.setdefault(requirement_id, []).extend(planned_ids)
    for rid, ids in mapping.items():
        mapping[rid] = sorted(set(ids))
    return mapping


def _count_test_statuses(results: list[TestCaseResult]) -> dict[str, int]:
    """Count test statuses from junit results."""

    counts = {"PASS": 0, "FAIL": 0, "SKIP": 0, "XFAIL": 0}
    for result in results:
        counts[result.status] += 1
    return counts


def _coverage_by_module(path: Path, modules: list[str]) -> dict[str, dict[str, float]]:
    """Parse coverage XML and return line/branch rates per module."""

    tree = ET.parse(path)
    root = tree.getroot()

    def normalize(filename: str) -> str:
        normalized = filename.replace("\\", "/")
        if normalized.startswith("./"):
            normalized = normalized[2:]
        if normalized.startswith("src/"):
            normalized = normalized[4:]
        return normalized

    module_rates: dict[str, dict[str, float]] = {
        module: {"line_rate": 0.0, "branch_rate": 0.0} for module in modules
    }
    for class_node in root.iter("class"):
        filename = class_node.get("filename")
        if not filename:
            continue
        normalized = normalize(filename)
        if normalized in module_rates:
            line_rate = float(class_node.get("line-rate", 0.0))
            branch_rate = float(class_node.get("branch-rate", 0.0))
            module_rates[normalized] = {
                "line_rate": line_rate,
                "branch_rate": branch_rate,
            }
    return module_rates


def _overall_coverage(path: Path) -> dict[str, float]:
    """Parse overall coverage line/branch rates."""

    tree = ET.parse(path)
    root = tree.getroot()
    return {
        "line_rate": float(root.get("line-rate", 0.0)),
        "branch_rate": float(root.get("branch-rate", 0.0)),
    }


def _load_json_array(path: Path) -> list[str]:
    """Load a JSON array file."""

    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [str(item) for item in data]
    return []


def main() -> int:
    """Main entry point."""

    args = parse_args()

    junit_results = _parse_junit(args.junit_xml)
    status_counts = _count_test_statuses(junit_results)

    requirement_ids = _parse_requirements(args.requirements)
    trace_rows = _read_traceability(args.traceability)
    planned_by_req = _planned_tests_by_requirement(trace_rows)

    passing_tests: set[str] = set()
    for result in junit_results:
        if result.status != "PASS":
            continue
        for requirement_id, planned_ids in planned_by_req.items():
            for planned_id in planned_ids:
                normalized = _normalize_test_id(planned_id)
                if planned_id in result.name or normalized in result.name:
                    passing_tests.add(planned_id)

    per_requirement: dict[str, dict[str, object]] = {}
    uncovered: list[str] = []
    covered_count = 0
    for requirement_id in sorted(requirement_ids):
        planned_ids = planned_by_req.get(requirement_id, [])
        has_passing = any(pid in passing_tests for pid in planned_ids)
        if has_passing:
            covered_count += 1
        else:
            uncovered.append(requirement_id)
        per_requirement[requirement_id] = {
            "planned_test_ids": planned_ids,
            "has_passing_test": has_passing,
        }

    requirements_total = len(requirement_ids)
    covered_percent = (
        (covered_count / requirements_total) * 100
        if requirements_total
        else 0.0
    )

    modules = [
        "orderflow/service.py",
        "orderflow/parser.py",
        "orderflow/validation.py",
        "orderflow/cli.py",
        "orderflow/store/sqlite.py",
    ]

    metrics = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "counts": {
            "tests_total": len(junit_results),
            "tests_pass": status_counts["PASS"],
            "tests_fail": status_counts["FAIL"],
            "tests_skip": status_counts["SKIP"],
            "tests_xfail": status_counts["XFAIL"],
        },
        "requirements_coverage": {
            "requirements_total": requirements_total,
            "requirements_covered": covered_count,
            "requirements_covered_percent": round(covered_percent, 2),
            "uncovered_requirement_ids": uncovered,
            "per_requirement": per_requirement,
        },
        "structural_coverage": {
            "overall": _overall_coverage(args.coverage_xml),
            "by_module": _coverage_by_module(args.coverage_xml, modules),
        },
        "combinatorial": {
            "cases_path": "docs/lo3/artifacts/combinatorial_cases.json",
        },
        "model": {
            "coverage_path": "docs/lo3/artifacts/model_coverage.json",
        },
        "yield": {
            "error_codes_exercised": sorted(_load_json_array(args.error_codes)),
            "performance_smoke_path": "docs/lo3/artifacts/performance_smoke.json",
        },
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(metrics, sort_keys=True, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
