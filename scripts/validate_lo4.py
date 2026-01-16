"""Validate LO4 evidence outputs."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


REQUIRED_ARTIFACTS = [
    "targets.json",
    "comparison.json",
    "coverage_from_lo3.json",
    "failure_modes_from_lo3.json",
    "performance_samples.json",
    "performance_stats.json",
    "environment.json",
]


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", required=True, help="Path to results_summary.md.")
    parser.add_argument("--log", required=True, help="Path to results_log.md.")
    parser.add_argument("--artifacts", required=True, help="Path to artifacts directory.")
    return parser


def _load_json(path: Path) -> Dict[str, Any]:
    """Load JSON from disk."""

    return json.loads(path.read_text(encoding="utf-8"))


def _check_required_files(artifacts_dir: Path, summary: Path, log: Path) -> List[str]:
    """Return a list of missing required files."""

    missing = []
    for name in REQUIRED_ARTIFACTS:
        if not (artifacts_dir / name).exists():
            missing.append(name)
    if not summary.exists():
        missing.append(str(summary))
    if not log.exists():
        missing.append(str(log))
    return missing


def _validate_targets_schema(payload: Dict[str, Any]) -> None:
    """Validate the targets.json schema."""

    if "requirements_coverage" not in payload:
        raise ValueError("targets.json missing requirements_coverage.")
    if "structural_coverage" not in payload:
        raise ValueError("targets.json missing structural_coverage.")
    if "failure_modes" not in payload:
        raise ValueError("targets.json missing failure_modes.")
    if "performance" not in payload:
        raise ValueError("targets.json missing performance.")
    batch_targets = payload.get("performance", {}).get("batch", {})
    if "minimum" not in batch_targets or "stretch" not in batch_targets:
        raise ValueError("targets.json missing batch minimum/stretch tiers.")
    throughput_targets = batch_targets.get("throughput", {})
    if "minimum" not in throughput_targets or "stretch" not in throughput_targets:
        raise ValueError("targets.json missing batch throughput tiers.")


def _validate_comparison_schema(payload: Dict[str, Any]) -> None:
    """Validate the comparison.json schema."""

    required = {"requirements_coverage", "structural_coverage", "failure_modes", "performance"}
    missing = required - set(payload.keys())
    if missing:
        raise ValueError(f"comparison.json missing keys: {sorted(missing)}")


def _validate_summary_sections(summary_text: str) -> None:
    """Ensure summary contains required headings."""

    required_sections = [
        "# LO4 Results Summary",
        "## Reproducibility and Integrity Checks",
        "## LO4.1 Gaps and Omissions",
        "## LO4.2 Targets and Motivation",
        "## LO4.3 Achieved vs Target Comparison",
        "## LO4.4 Actions Needed to Meet/Exceed Targets",
        "## Overall Confidence Statement",
    ]
    for section in required_sections:
        if section not in summary_text:
            raise ValueError(f"Missing summary section: {section}")

    required_gap_phrases = [
        "Missing failure modes",
        "Performance targets not met",
        "operational envelope",
        "subprocess",
        "exception/fault",
        "mutation",
        "Statistical assumptions",
    ]
    for phrase in required_gap_phrases:
        if phrase not in summary_text:
            raise ValueError(f"Missing required gap topic in LO4.1 table: {phrase}")


def _validate_throughput_stats(targets: Dict[str, Any], stats: Dict[str, Any]) -> None:
    """Validate throughput stats presence when throughput targets exist."""

    throughput_targets = (
        targets.get("performance", {}).get("batch", {}).get("throughput", {})
    )
    if throughput_targets:
        throughput_stats = stats.get("batch", {}).get("throughput")
        if not throughput_stats:
            raise ValueError("performance_stats.json missing batch throughput stats.")
        required_keys = {
            "mean_lines_per_sec",
            "median_lines_per_sec",
            "stdev_lines_per_sec",
            "ci_mean_lines_per_sec",
        }
        missing = required_keys - set(throughput_stats.keys())
        if missing:
            raise ValueError(
                f"performance_stats.json throughput stats missing keys: {sorted(missing)}"
            )


def _assert_lo3_clean() -> None:
    """Ensure docs/lo3 has no uncommitted changes."""

    result = subprocess.run(
        ["git", "diff", "--name-only", "--", "docs/lo3"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.stdout.strip():
        raise RuntimeError("docs/lo3 has uncommitted changes.")


def main() -> None:
    """CLI entry point."""

    parser = _build_parser()
    args = parser.parse_args()

    summary_path = Path(args.summary)
    log_path = Path(args.log)
    artifacts_dir = Path(args.artifacts)

    missing = _check_required_files(artifacts_dir, summary_path, log_path)
    if missing:
        raise FileNotFoundError(f"Missing required LO4 outputs: {missing}")

    targets = _load_json(artifacts_dir / "targets.json")
    comparison = _load_json(artifacts_dir / "comparison.json")
    performance_stats = _load_json(artifacts_dir / "performance_stats.json")
    _validate_targets_schema(targets)
    _validate_comparison_schema(comparison)
    _validate_throughput_stats(targets, performance_stats)

    summary_text = summary_path.read_text(encoding="utf-8")
    _validate_summary_sections(summary_text)
    _assert_lo3_clean()

    print("LO4 validation OK.")


if __name__ == "__main__":
    main()
