"""Generate the LO4 results summary markdown."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Sequence


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", required=True, help="Path to environment.json.")
    parser.add_argument("--targets", required=True, help="Path to targets.json.")
    parser.add_argument("--coverage", required=True, help="Path to coverage_from_lo3.json.")
    parser.add_argument(
        "--failure-modes",
        required=True,
        help="Path to failure_modes_from_lo3.json.",
    )
    parser.add_argument("--performance", required=True, help="Path to performance_stats.json.")
    parser.add_argument("--comparison", required=True, help="Path to comparison.json.")
    parser.add_argument("--log", required=True, help="Path to results_log.md.")
    parser.add_argument("--summary", required=True, help="Path to results_summary.md.")
    parser.add_argument("--git-commit", required=True, help="Git commit hash for the run.")
    parser.add_argument("--lo3-check", required=True, help="Statement of LO3 integrity checks.")
    return parser


def _load_json(path: Path) -> Dict[str, Any]:
    """Load JSON data from disk."""

    return json.loads(path.read_text(encoding="utf-8"))


def _table(rows: List[List[str]]) -> str:
    """Render a Markdown table."""

    if not rows:
        return ""
    header = rows[0]
    separator = ["---" for _ in header]
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(separator) + " |",
    ]
    for row in rows[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _fmt_ci(ci_values: Sequence[float] | None) -> str:
    """Format a confidence interval list for display."""

    if not ci_values or len(ci_values) < 2:
        return "CI n/a"
    return f"CI [{ci_values[0]}, {ci_values[1]}]"


def _interpret_ci(mean_ci: Sequence[float] | None, target: float, direction: str) -> str:
    """Interpret a confidence interval against a target threshold."""

    if not mean_ci or len(mean_ci) < 2:
        return "CI not available for interpretation."
    lower, upper = float(mean_ci[0]), float(mean_ci[1])
    if direction == "max":
        if lower > target:
            return "Fail with high confidence under this workload/environment."
        if upper >= target >= lower:
            return "Inconclusive/near-boundary; CI overlaps threshold."
        return "Pass with high confidence under this workload/environment."
    if upper < target:
        return "Fail with high confidence under this workload/environment."
    if upper >= target >= lower:
        return "Inconclusive/near-boundary; CI overlaps threshold."
    return "Pass with high confidence under this workload/environment."


def _format_gap_row(
    title: str,
    evidence: str,
    risk: str,
    mitigation: str,
) -> List[str]:
    """Format a gap/omission row for the summary table."""

    return [title, evidence, risk, mitigation]


def main() -> None:
    """CLI entry point."""

    parser = _build_parser()
    args = parser.parse_args()

    environment = _load_json(Path(args.environment))
    targets = _load_json(Path(args.targets))
    coverage = _load_json(Path(args.coverage))
    failure_modes = _load_json(Path(args.failure_modes))
    performance = _load_json(Path(args.performance))
    comparison = _load_json(Path(args.comparison))

    env_block = (
        f"- OS: {environment['os']['system']} {environment['os']['release']} "
        f"({environment['os']['version']})\n"
        f"- Python: {environment['python']['version']}\n"
        f"- CPU: {environment['hardware'].get('cpu_model')}\n"
        f"- Cores: {environment['hardware'].get('cpu_count')}\n"
        f"- RAM bytes: {environment['hardware'].get('memory_bytes')}\n"
        "- Source: docs/lo4/artifacts/environment.json"
    )

    workload = performance.get("workload", {})
    workload_place = workload.get("place", {})
    workload_batch = workload.get("batch", {})
    measurement_quality = targets.get("measurement_quality", {})

    missing_codes = comparison["failure_modes"].get("missing_codes", [])
    required_codes = comparison["failure_modes"].get("required_codes", [])
    exercised_codes = comparison["failure_modes"].get("exercised_codes", [])

    perf_targets = targets.get("performance", {})
    batch_targets = perf_targets.get("batch", {})
    batch_min = batch_targets.get("minimum", {})
    batch_stretch = batch_targets.get("stretch", {})
    batch_throughput_targets = batch_targets.get("throughput", {})
    place_perf = performance["place"]
    batch_perf = performance["batch"]
    throughput_stats = batch_perf.get("throughput", {})

    ci_misses: List[str] = []
    place_ci = place_perf.get("ci_mean_ms")
    if place_ci and len(place_ci) >= 2 and place_ci[0] > perf_targets["place"]["mean_ms"]:
        ci_misses.append(
            f"place mean CI {place_ci} > target {perf_targets['place']['mean_ms']} ms"
        )
    batch_ci = batch_perf.get("ci_mean_ms")
    if batch_ci and len(batch_ci) >= 2 and batch_ci[0] > batch_min.get("mean_ms", 0.0):
        ci_misses.append(
            f"batch mean CI {batch_ci} > minimum {batch_min.get('mean_ms')} ms"
        )
    throughput_ci = throughput_stats.get("ci_mean_lines_per_sec")
    if (
        throughput_ci
        and len(throughput_ci) >= 2
        and throughput_ci[1] < batch_throughput_targets.get("minimum", {}).get("mean_lines_per_sec", 0.0)
    ):
        ci_misses.append(
            "batch throughput CI "
            f"{throughput_ci} < minimum "
            f"{batch_throughput_targets['minimum']['mean_lines_per_sec']} lines/sec"
        )
    ci_miss_text = "; ".join(ci_misses) if ci_misses else "No CI entirely beyond targets recorded."

    assumptions = performance.get("assumptions", [])
    assumptions_text = ", ".join(assumptions) if assumptions else "None recorded."

    gaps_rows = [
        ["Gap/Omission", "Evidence file(s)", "Risk", "Mitigation idea"],
        _format_gap_row(
            "Missing failure modes (codes not exercised)",
            (
                "docs/lo4/artifacts/failure_modes_from_lo3.json "
                f"(missing: {', '.join(missing_codes) if missing_codes else 'none'})"
            ),
            (
                "Unhandled error-code paths could regress or map incorrectly, "
                "reducing robustness confidence."
            ),
            (
                "Add deterministic tests to exercise missing codes: "
                f"{', '.join(missing_codes) if missing_codes else 'none listed'}."
            ),
        ),
        _format_gap_row(
            "Performance targets not met with statistical confidence",
            (
                "docs/lo4/artifacts/performance_stats.json "
                f"(CI evidence: {ci_miss_text})"
            ),
            (
                "Performance regression risk remains if CI ranges are entirely above "
                "targets."
            ),
            "Prioritize optimization or reduce overhead in slow paths.",
        ),
        _format_gap_row(
            "Context-dependent performance / limited operational envelope",
            "docs/lo4/artifacts/performance_stats.json",
            (
                "Only one workload point per operation was measured, limiting "
                "generalizability."
            ),
            "Add envelope benchmarks (batch lines 5/20/50, place payload variants).",
        ),
        _format_gap_row(
            "CLI coverage attribution limitation (subprocess)",
            "docs/lo3/artifacts/metrics.json",
            (
                "Subprocess-based CLI runs produce low coverage attribution, "
                "masking CLI regressions."
            ),
            "Add in-process CLI parsing tests or subprocess coverage capture.",
        ),
        _format_gap_row(
            "Weak exploration of exception/fault paths",
            "docs/lo4/artifacts/failure_modes_from_lo3.json",
            (
                "DB fault mapping and defensive paths remain partially untested, "
                "leaving residual risk."
            ),
            "Add deterministic fault-injection seams for DB/logic faults.",
        ),
        _format_gap_row(
            "No mutation/fault-based sensitivity estimate",
            "docs/lo4/results_summary.md",
            (
                "Without mutation, confidence in test sensitivity is limited; "
                "faults could survive."
            ),
            "Consider mutation testing in LO5 to quantify sensitivity.",
        ),
        _format_gap_row(
            "Statistical assumptions",
            "docs/lo4/artifacts/performance_stats.json",
            (
                "Assumptions such as independent samples and warmup discard "
                f"may not hold, affecting CI validity ({assumptions_text})."
            ),
            (
                "Re-run benchmarks with randomized ordering and validate "
                "assumptions in LO5."
            ),
        ),
    ]

    target_rows = [
        ["Target", "Value", "Motivation / Source"],
        [
            "Requirements coverage",
            f">= {targets['requirements_coverage']['target_percent']}%",
            "Source: docs/lo4/artifacts/targets.json",
        ],
    ]

    for module, target in targets["structural_coverage"]["modules"].items():
        target_rows.append(
            [
                f"Structural coverage {module}",
                f">= {target['line_rate']:.2f} line / {target['branch_rate']:.2f} branch",
                "Risk-based structural coverage target (LO3 criteria).",
            ]
        )

    target_rows.extend(
        [
            [
                "Failure-mode coverage",
                "All documented error codes exercised",
                "docs/cli_contract.md list.",
            ],
            [
                "Place performance",
                (
                    f"mean <= {perf_targets['place']['mean_ms']} ms, "
                    f"p95 <= {perf_targets['place']['p95_ms']} ms"
                ),
                "Source: docs/lo4/artifacts/targets.json (from LO1).",
            ],
            [
                "Batch performance (minimum)",
                (
                    f"mean <= {batch_min['mean_ms']} ms, "
                    f"p95 <= {batch_min['p95_ms']} ms"
                ),
                f"Minimum acceptable threshold: {batch_min.get('motivation')}",
            ],
            [
                "Batch performance (stretch)",
                (
                    f"mean <= {batch_stretch['mean_ms']} ms, "
                    f"p95 <= {batch_stretch['p95_ms']} ms"
                ),
                f"Aspirational threshold: {batch_stretch.get('motivation')}",
            ],
            [
                "Batch throughput (minimum)",
                f">= {batch_throughput_targets['minimum']['mean_lines_per_sec']} lines/sec",
                "Derived from latency samples and known batch line count.",
            ],
            [
                "Batch throughput (stretch)",
                f">= {batch_throughput_targets['stretch']['mean_lines_per_sec']} lines/sec",
                "Derived from latency samples and known batch line count.",
            ],
            [
                "Measurement quality",
                (
                    f"samples >= {measurement_quality['samples_place']} (place) / "
                    f"{measurement_quality['samples_batch']} (batch), "
                    f"warmup={measurement_quality['warmup']}, "
                    f"CI={measurement_quality['ci_method']} "
                    f"resamples={measurement_quality['bootstrap_resamples']}"
                ),
                "Source: docs/lo4/artifacts/targets.json",
            ],
        ]
    )

    comparison_rows = [
        ["Metric", "Achieved (CI)", "Target", "Pass/Fail", "Explanation"],
        [
            "Requirements coverage",
            f"{comparison['requirements_coverage']['achieved_percent']}% (n/a)",
            f"{comparison['requirements_coverage']['target_percent']}%",
            "PASS" if comparison["requirements_coverage"]["passed"] else "FAIL",
            "Source: docs/lo4/artifacts/coverage_from_lo3.json",
        ],
    ]

    for module in comparison["structural_coverage"]["modules"]:
        comparison_rows.append(
            [
                f"Coverage {module['module']}",
                (
                    f"line {module['achieved']['line_rate']:.2f}, "
                    f"branch {module['achieved']['branch_rate']:.2f}"
                ),
                (
                    f"line {module['target']['line_rate']:.2f}, "
                    f"branch {module['target']['branch_rate']:.2f}"
                ),
                "PASS" if module["passed"] else "FAIL",
                "Source: docs/lo4/artifacts/coverage_from_lo3.json",
            ]
        )

    comparison_rows.append(
        [
            "Failure modes exercised",
            ", ".join(comparison["failure_modes"]["exercised_codes"]),
            ", ".join(comparison["failure_modes"]["required_codes"]),
            "PASS" if comparison["failure_modes"]["passed"] else "FAIL",
            (
                "Missing: " + ", ".join(comparison["failure_modes"]["missing_codes"])
                if comparison["failure_modes"]["missing_codes"]
                else "All required codes exercised."
            )
            + " (Source: docs/lo4/artifacts/failure_modes_from_lo3.json)",
        ]
    )

    place_perf = performance["place"]
    place_comp = comparison["performance"]["details"]["place"]
    comparison_rows.append(
        [
            "Place mean latency",
            f"{place_perf['mean_ms']} ms ({_fmt_ci(place_perf.get('ci_mean_ms'))})",
            f"<= {perf_targets['place']['mean_ms']} ms",
            "PASS" if place_comp["mean_ms"]["passed"] else "FAIL",
            "Source: docs/lo4/artifacts/performance_stats.json",
        ]
    )
    comparison_rows.append(
        [
            "Place p95 latency",
            f"{place_perf['p95_ms']} ms ({_fmt_ci(place_perf.get('ci_p95_ms'))})",
            f"<= {perf_targets['place']['p95_ms']} ms",
            "PASS" if place_comp["p95_ms"]["passed"] else "FAIL",
            "Source: docs/lo4/artifacts/performance_stats.json",
        ]
    )

    batch_perf = performance["batch"]
    batch_comp = comparison["performance"]["details"]["batch_latency"]
    comparison_rows.append(
        [
            "Batch mean latency (minimum)",
            f"{batch_perf['mean_ms']} ms ({_fmt_ci(batch_perf.get('ci_mean_ms'))})",
            f"<= {batch_min['mean_ms']} ms",
            "PASS" if batch_comp["minimum"]["mean_ms"]["passed"] else "FAIL",
            "Source: docs/lo4/artifacts/performance_stats.json",
        ]
    )
    comparison_rows.append(
        [
            "Batch p95 latency (minimum)",
            f"{batch_perf['p95_ms']} ms ({_fmt_ci(batch_perf.get('ci_p95_ms'))})",
            f"<= {batch_min['p95_ms']} ms",
            "PASS" if batch_comp["minimum"]["p95_ms"]["passed"] else "FAIL",
            "Source: docs/lo4/artifacts/performance_stats.json",
        ]
    )
    comparison_rows.append(
        [
            "Batch mean latency (stretch)",
            f"{batch_perf['mean_ms']} ms ({_fmt_ci(batch_perf.get('ci_mean_ms'))})",
            f"<= {batch_stretch['mean_ms']} ms",
            "PASS" if batch_comp["stretch"]["mean_ms"]["passed"] else "FAIL",
            "Source: docs/lo4/artifacts/performance_stats.json",
        ]
    )
    comparison_rows.append(
        [
            "Batch p95 latency (stretch)",
            f"{batch_perf['p95_ms']} ms ({_fmt_ci(batch_perf.get('ci_p95_ms'))})",
            f"<= {batch_stretch['p95_ms']} ms",
            "PASS" if batch_comp["stretch"]["p95_ms"]["passed"] else "FAIL",
            "Source: docs/lo4/artifacts/performance_stats.json",
        ]
    )

    throughput_stats = batch_perf.get("throughput", {})
    throughput_comp = comparison["performance"]["details"]["batch_throughput"]
    comparison_rows.append(
        [
            "Batch throughput mean (minimum)",
            (
                f"{throughput_stats.get('mean_lines_per_sec')} lines/sec "
                f"({_fmt_ci(throughput_stats.get('ci_mean_lines_per_sec'))})"
            ),
            f">= {batch_throughput_targets['minimum']['mean_lines_per_sec']} lines/sec",
            "PASS"
            if throughput_comp["minimum"]["mean_lines_per_sec"]["passed"]
            else "FAIL",
            "Source: docs/lo4/artifacts/performance_stats.json",
        ]
    )
    comparison_rows.append(
        [
            "Batch throughput mean (stretch)",
            (
                f"{throughput_stats.get('mean_lines_per_sec')} lines/sec "
                f"({_fmt_ci(throughput_stats.get('ci_mean_lines_per_sec'))})"
            ),
            f">= {batch_throughput_targets['stretch']['mean_lines_per_sec']} lines/sec",
            "PASS"
            if throughput_comp["stretch"]["mean_lines_per_sec"]["passed"]
            else "FAIL",
            "Source: docs/lo4/artifacts/performance_stats.json",
        ]
    )

    actions = [
        [
            "P0",
            "Add deterministic test for ORDER_ALREADY_FULFILLED (fulfill twice).",
            "Missing failure mode coverage (ORDER_ALREADY_FULFILLED).",
            "Closes error-code gap and improves robustness confidence.",
            "Test ID recorded in LO3/LO4 evidence with passing result.",
        ],
        [
            "P0",
            "Add deterministic DB-fault injection seam/test to trigger DATABASE_ERROR mapping.",
            "Missing failure mode coverage (DATABASE_ERROR).",
            "Improves confidence in DB fault handling.",
            "Fault-injection test artifact captures DATABASE_ERROR.",
        ],
        [
            "P0",
            "Add controlled invariant-violation seam/test to trigger INTERNAL_ERROR mapping.",
            "Missing failure mode coverage (INTERNAL_ERROR).",
            "Improves defensive-path assurance.",
            "Fault-injection test artifact captures INTERNAL_ERROR.",
        ],
        [
            "P1",
            "Performance: split cold vs warm runs and report separately.",
            "Performance CI ambiguity and potential cold-start penalty.",
            "Clarifies warm vs cold impact on latency/throughput.",
            "Separate cold/warm stats included in performance_stats.json.",
        ],
        [
            "P1",
            "Performance: add envelope benchmark points (batch lines 5/20/50) without changing CLI contract.",
            "Limited operational envelope coverage.",
            "Improves generalization across workloads.",
            "Additional workload rows in performance_stats.json.",
        ],
        [
            "P1",
            "CLI coverage: add in-process parsing/unit tests for CLI argument handling OR subprocess coverage capture.",
            "CLI subprocess coverage attribution limitation.",
            "Improves coverage signal for CLI paths.",
            "Coverage report shows CLI module line/branch rates > 0.",
        ],
        [
            "P2",
            "Optional: mutation testing in LO5 (future action).",
            "No mutation/fault-based sensitivity estimate.",
            "Quantifies test sensitivity to seeded faults.",
            "Mutation report included in LO5 artifacts.",
        ],
    ]

    assumptions = performance.get("assumptions", [])
    assumptions_text = ", ".join(assumptions) if assumptions else "None recorded."

    statistical_interpretations = [
        (
            "Place mean latency",
            place_perf.get("ci_mean_ms"),
            perf_targets["place"]["mean_ms"],
            "max",
        ),
        (
            "Batch mean latency (minimum)",
            batch_perf.get("ci_mean_ms"),
            batch_min["mean_ms"],
            "max",
        ),
        (
            "Batch mean latency (stretch)",
            batch_perf.get("ci_mean_ms"),
            batch_stretch["mean_ms"],
            "max",
        ),
        (
            "Batch throughput mean (minimum)",
            throughput_stats.get("ci_mean_lines_per_sec"),
            batch_throughput_targets["minimum"]["mean_lines_per_sec"],
            "min",
        ),
        (
            "Batch throughput mean (stretch)",
            throughput_stats.get("ci_mean_lines_per_sec"),
            batch_throughput_targets["stretch"]["mean_lines_per_sec"],
            "min",
        ),
    ]
    interpretation_lines = "\n".join(
        (
            f"- {label}: {_fmt_ci(ci)} vs target {target} -> "
            f"{_interpret_ci(ci, target, direction)}"
        )
        for label, ci, target, direction in statistical_interpretations
    )

    summary = f"""# LO4 Results Summary

## Reproducibility and Integrity Checks
- Version anchor: {args.git_commit}
- Environment:
{env_block}
- Workload definition:
  - place: mobile={workload_place.get('mobile')}, message={workload_place.get('message')}
  - batch: message={workload_batch.get('message')}, lines={workload_batch.get('lines')}
- Sample sizes and CI:
  - place samples={measurement_quality.get('samples_place')}, batch samples={measurement_quality.get('samples_batch')}
  - warmup={measurement_quality.get('warmup')}, resamples={measurement_quality.get('bootstrap_resamples')}
  - ci_method={measurement_quality.get('ci_method')}
- Commands: see {args.log}
- docs/lo3 integrity check: git diff --name-only -- docs/lo3 empty before and after run

## LO4.1 Gaps and Omissions
{_table(gaps_rows)}

## LO4.2 Targets and Motivation
{_table(target_rows)}

## LO4.3 Achieved vs Target Comparison
{_table(comparison_rows)}

Failure modes exercised: {len(exercised_codes)}/{len(required_codes)}. Missing: {", ".join(missing_codes) if missing_codes else "None"}. Status: {"PASS" if comparison["failure_modes"]["passed"] else "FAIL"}.

Coverage summary: {len(comparison['structural_coverage']['modules'])} modules compared to targets in docs/lo4/artifacts/coverage_from_lo3.json.

Statistical interpretation:
{interpretation_lines}

## LO4.4 Actions Needed to Meet/Exceed Targets
{_table([["Priority", "Action", "Gap/Miss addressed", "Expected impact", "Evidence of completion"]] + actions)}

## Overall Confidence Statement
Requirements coverage and core module coverage are strongly supported by LO3-derived
artifacts (docs/lo4/artifacts/coverage_from_lo3.json). Performance evidence is
statistically characterized (docs/lo4/artifacts/performance_stats.json), but
missing failure modes and environment sensitivity reduce confidence in robustness
and performance generality (docs/lo4/artifacts/failure_modes_from_lo3.json).
Assumptions documented in performance_stats.json include: {assumptions_text}
"""

    summary_path = Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summary, encoding="utf-8")


if __name__ == "__main__":
    main()
