"""Compare LO4 achieved results against targets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--targets", required=True, help="Path to targets.json.")
    parser.add_argument("--coverage", required=True, help="Path to coverage_from_lo3.json.")
    parser.add_argument(
        "--failure-modes",
        required=True,
        help="Path to failure_modes_from_lo3.json.",
    )
    parser.add_argument("--performance", required=True, help="Path to performance_stats.json.")
    parser.add_argument("--output", required=True, help="Path to comparison.json.")
    return parser


def _load_json(path: Path) -> Dict[str, Any]:
    """Load JSON from disk."""

    return json.loads(path.read_text(encoding="utf-8"))


def _compare_requirements(targets: Dict[str, Any], coverage: Dict[str, Any]) -> Dict[str, Any]:
    """Compare requirements coverage target."""

    achieved = coverage.get("requirements_coverage", {})
    percent = achieved.get("requirements_covered_percent", 0.0)
    target_percent = targets.get("requirements_coverage", {}).get("target_percent", 0.0)
    passed = percent >= target_percent
    return {
        "target_percent": target_percent,
        "achieved_percent": percent,
        "passed": passed,
        "explanation": "LO3 traceability coverage percent compared to LO4 target.",
    }


def _compare_structural(targets: Dict[str, Any], coverage: Dict[str, Any]) -> Dict[str, Any]:
    """Compare structural coverage targets per module."""

    targets_by_module = targets.get("structural_coverage", {}).get("modules", {})
    achieved_by_module = coverage.get("structural_coverage", {}).get("by_module", {})
    comparisons: List[Dict[str, Any]] = []
    passed = True
    for module, target in targets_by_module.items():
        achieved = achieved_by_module.get(module, {})
        line_rate = achieved.get("line_rate", 0.0)
        branch_rate = achieved.get("branch_rate", 0.0)
        line_target = target.get("line_rate", 0.0)
        branch_target = target.get("branch_rate", 0.0)
        module_passed = line_rate >= line_target and branch_rate >= branch_target
        comparisons.append(
            {
                "module": module,
                "target": target,
                "achieved": {"line_rate": line_rate, "branch_rate": branch_rate},
                "passed": module_passed,
            }
        )
        passed = passed and module_passed
    return {
        "passed": passed,
        "modules": comparisons,
        "explanation": "Module-level line/branch coverage compared to LO3 targets.",
    }


def _compare_failure_modes(targets: Dict[str, Any], failure_modes: Dict[str, Any]) -> Dict[str, Any]:
    """Compare required failure modes."""

    required = set(targets.get("failure_modes", {}).get("required_codes", []))
    achieved = set(failure_modes.get("error_codes_exercised", []))
    missing = sorted(required - achieved)
    passed = not missing
    return {
        "required_codes": sorted(required),
        "achieved_codes": sorted(achieved),
        "missing_codes": missing,
        "passed": passed,
        "explanation": "Error-code coverage compared to LO4 target list.",
    }


def _compare_performance(targets: Dict[str, Any], perf: Dict[str, Any]) -> Dict[str, Any]:
    """Compare performance statistics to targets."""

    performance_targets = targets.get("performance", {})
    comparison = {}
    passed = True
    for series in ("place", "batch"):
        target = performance_targets.get(series, {})
        achieved = perf.get(series, {})
        mean_target = target.get("mean_ms")
        p95_target = target.get("p95_ms")
        mean_ms = achieved.get("mean_ms", 0.0)
        p95_ms = achieved.get("p95_ms", 0.0)
        series_passed = mean_ms <= mean_target and p95_ms <= p95_target
        comparison[series] = {
            "target": {"mean_ms": mean_target, "p95_ms": p95_target},
            "achieved": {"mean_ms": mean_ms, "p95_ms": p95_ms},
            "passed": series_passed,
        }
        passed = passed and series_passed
    return {
        "passed": passed,
        "series": comparison,
        "explanation": "Mean and p95 total latency compared to LO4 targets.",
    }


def main() -> None:
    """CLI entry point."""

    parser = _build_parser()
    args = parser.parse_args()
    targets = _load_json(Path(args.targets))
    coverage = _load_json(Path(args.coverage))
    failure_modes = _load_json(Path(args.failure_modes))
    performance = _load_json(Path(args.performance))

    payload = {
        "requirements_coverage": _compare_requirements(targets, coverage),
        "structural_coverage": _compare_structural(targets, coverage),
        "failure_modes": _compare_failure_modes(targets, failure_modes),
        "performance": _compare_performance(targets, performance),
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
