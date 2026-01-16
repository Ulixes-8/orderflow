"""Compare LO4 achieved results against targets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Literal


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
        "exercised_codes": sorted(achieved),
        "missing_codes": missing,
        "passed": passed,
        "explanation": "Error-code coverage compared to LO4 target list.",
    }


def _compare_metric(
    achieved: float,
    target: float,
    direction: Literal["max", "min"],
) -> Dict[str, Any]:
    """Compare an achieved value against a target threshold."""

    if direction == "max":
        passed = achieved <= target
        relation = "<="
    else:
        passed = achieved >= target
        relation = ">="
    return {
        "achieved": achieved,
        "target": target,
        "relation": relation,
        "passed": passed,
    }


def _compare_performance(targets: Dict[str, Any], perf: Dict[str, Any]) -> Dict[str, Any]:
    """Compare performance statistics to targets."""

    performance_targets = targets.get("performance", {})
    place_target = performance_targets.get("place", {})
    batch_target = performance_targets.get("batch", {})

    place_stats = perf.get("place", {})
    batch_stats = perf.get("batch", {})

    comparison: Dict[str, Any] = {
        "place": {
            "mean_ms": _compare_metric(
                place_stats.get("mean_ms", 0.0),
                place_target.get("mean_ms", 0.0),
                "max",
            ),
            "p95_ms": _compare_metric(
                place_stats.get("p95_ms", 0.0),
                place_target.get("p95_ms", 0.0),
                "max",
            ),
            "ci_mean_ms": place_stats.get("ci_mean_ms"),
            "ci_p95_ms": place_stats.get("ci_p95_ms"),
        },
        "batch_latency": {},
        "batch_throughput": {},
    }

    batch_min = batch_target.get("minimum", {})
    batch_stretch = batch_target.get("stretch", {})
    batch_throughput_targets = batch_target.get("throughput", {})
    throughput_stats = batch_stats.get("throughput", {})

    comparison["batch_latency"]["minimum"] = {
        "mean_ms": _compare_metric(
            batch_stats.get("mean_ms", 0.0),
            batch_min.get("mean_ms", 0.0),
            "max",
        ),
        "p95_ms": _compare_metric(
            batch_stats.get("p95_ms", 0.0),
            batch_min.get("p95_ms", 0.0),
            "max",
        ),
        "ci_mean_ms": batch_stats.get("ci_mean_ms"),
        "ci_p95_ms": batch_stats.get("ci_p95_ms"),
    }
    comparison["batch_latency"]["stretch"] = {
        "mean_ms": _compare_metric(
            batch_stats.get("mean_ms", 0.0),
            batch_stretch.get("mean_ms", 0.0),
            "max",
        ),
        "p95_ms": _compare_metric(
            batch_stats.get("p95_ms", 0.0),
            batch_stretch.get("p95_ms", 0.0),
            "max",
        ),
        "ci_mean_ms": batch_stats.get("ci_mean_ms"),
        "ci_p95_ms": batch_stats.get("ci_p95_ms"),
    }

    comparison["batch_throughput"]["minimum"] = {
        "mean_lines_per_sec": _compare_metric(
            throughput_stats.get("mean_lines_per_sec", 0.0),
            batch_throughput_targets.get("minimum", {}).get("mean_lines_per_sec", 0.0),
            "min",
        ),
        "ci_mean_lines_per_sec": throughput_stats.get("ci_mean_lines_per_sec"),
    }
    comparison["batch_throughput"]["stretch"] = {
        "mean_lines_per_sec": _compare_metric(
            throughput_stats.get("mean_lines_per_sec", 0.0),
            batch_throughput_targets.get("stretch", {}).get("mean_lines_per_sec", 0.0),
            "min",
        ),
        "ci_mean_lines_per_sec": throughput_stats.get("ci_mean_lines_per_sec"),
    }

    passed = (
        comparison["place"]["mean_ms"]["passed"]
        and comparison["place"]["p95_ms"]["passed"]
        and comparison["batch_latency"]["minimum"]["mean_ms"]["passed"]
        and comparison["batch_latency"]["minimum"]["p95_ms"]["passed"]
        and comparison["batch_latency"]["stretch"]["mean_ms"]["passed"]
        and comparison["batch_latency"]["stretch"]["p95_ms"]["passed"]
        and comparison["batch_throughput"]["minimum"]["mean_lines_per_sec"]["passed"]
        and comparison["batch_throughput"]["stretch"]["mean_lines_per_sec"]["passed"]
    )

    return {
        "passed": passed,
        "details": comparison,
        "explanation": (
            "Place mean/p95 compared to targets; batch latency evaluated "
            "against minimum and stretch tiers; throughput evaluated against "
            "minimum and stretch lines/sec targets."
        ),
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
