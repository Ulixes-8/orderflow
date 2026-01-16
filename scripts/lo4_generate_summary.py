"""Generate the LO4 results summary markdown."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


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

    gaps_rows = [
        ["Gap / Omission", "Evidence", "Risk", "Mitigation"],
        [
            "No mutation testing",
            "Not present in docs/lo4/artifacts",
            "Weak oracles may mask faults",
            "Add mutation testing or stronger assertions in LO5",
        ],
        [
            "CLI subprocess coverage is low",
            "docs/lo3/artifacts/coverage.xml",
            "CLI paths could regress without structural signal",
            "Extend CLI-level contract tests and diagnostics",
        ],
    ]

    target_rows = [
        ["Target", "Value", "Motivation / Source"],
        [
            "Requirements coverage",
            f">= {targets['requirements_coverage']['target_percent']}%",
            "Source: docs/lo4/artifacts/targets.json",
        ],
        [
            "Parser line/branch",
            ">= 90% / 75%",
            "Risk-based structural coverage target (LO3 criteria).",
        ],
        [
            "Validation line/branch",
            ">= 90% / 75%",
            "Risk-based structural coverage target (LO3 criteria).",
        ],
        [
            "SQLite repo line/branch",
            ">= 80% / 70%",
            "Risk-based structural coverage target (LO3 criteria).",
        ],
        [
            "Service line/branch",
            ">= 65% / 50%",
            "Risk-based structural coverage target (LO3 criteria).",
        ],
        [
            "Failure-mode coverage",
            "All documented error codes exercised",
            "docs/cli_contract.md list.",
        ],
        [
            "Place performance",
            (
                f"mean <= {targets['performance']['place']['mean_ms']} ms, "
                f"p95 <= {targets['performance']['place']['p95_ms']} ms"
            ),
            "Source: docs/lo4/artifacts/targets.json (from LO1).",
        ],
        [
            "Batch performance",
            (
                f"mean <= {targets['performance']['batch']['mean_ms']} ms, "
                f"p95 <= {targets['performance']['batch']['p95_ms']} ms"
            ),
            "Source: docs/lo4/artifacts/targets.json",
        ],
        [
            "Measurement quality",
            (
                f"samples >= {targets['measurement_quality']['samples_place']} "
                f"(place) / {targets['measurement_quality']['samples_batch']} (batch), "
                f"warmup={targets['measurement_quality']['warmup']}, "
                f"CI={targets['measurement_quality']['ci_method']}"
            ),
            "Source: docs/lo4/artifacts/targets.json",
        ],
    ]

    comparison_rows = [
        ["Metric", "Achieved", "Target", "Pass/Fail", "Explanation"],
        [
            "Requirements coverage",
            f"{comparison['requirements_coverage']['achieved_percent']}%",
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
            ", ".join(comparison["failure_modes"]["achieved_codes"]),
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

    for series in ("place", "batch"):
        comparison_rows.append(
            [
                f"Performance {series}",
                (
                    f"mean {performance[series]['mean_ms']} ms, "
                    f"p95 {performance[series]['p95_ms']} ms "
                    f"(n={performance[series]['n']})"
                ),
                (
                    f"mean <= {targets['performance'][series]['mean_ms']} ms, "
                    f"p95 <= {targets['performance'][series]['p95_ms']} ms"
                ),
                "PASS" if comparison["performance"]["series"][series]["passed"] else "FAIL",
                "Source: docs/lo4/artifacts/performance_stats.json",
            ]
        )

    actions = [
        [
            "P0",
            "Add tests for missing error codes or coverage gaps.",
            "Improves failure-mode and structural coverage targets.",
        ],
        [
            "P1",
            "Introduce mutation testing or stronger oracles.",
            "Raises confidence beyond coverage metrics.",
        ],
        [
            "P2",
            "Automate performance regression alerts.",
            "Maintains LO4 performance targets over time.",
        ],
    ]

    summary = f"""# LO4 Results Summary

## Reproducibility and Integrity Checks
- Version anchor: {args.git_commit}
- Environment:
{env_block}
- Commands: see {args.log}
- LO3 integrity check: {args.lo3_check}

## LO4.1 Gaps and Omissions
{_table(gaps_rows)}

## LO4.2 Targets and Motivation
{_table(target_rows)}

## LO4.3 Achieved vs Target Comparison
{_table(comparison_rows)}

Performance statistics (mean, median, stdev, p95, CI mean, CI p95) are in
docs/lo4/artifacts/performance_stats.json.

LO3-derived achievements (requirements coverage, structural coverage, error codes)
are sourced from docs/lo3/artifacts/metrics.json and
docs/lo3/artifacts/error_codes_exercised.json (no LO3 commit anchor is recorded in
LO3 docs; LO4 uses the current repository commit).

## LO4.4 Actions Needed to Meet/Exceed Targets
{_table([["Priority", "Action", "Expected Impact"]] + actions)}

## Overall Confidence Statement
Evidence supports high confidence in requirements coverage and core module
structural coverage from LO3 artifacts (docs/lo4/artifacts/coverage_from_lo3.json).
Performance evidence is statistically characterized (docs/lo4/artifacts/performance_stats.json)
but remains environment-sensitive. Residual risk remains around CLI subprocess
coverage and unexercised failure modes (docs/lo4/artifacts/failure_modes_from_lo3.json).
"""

    summary_path = Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summary, encoding="utf-8")


if __name__ == "__main__":
    main()
