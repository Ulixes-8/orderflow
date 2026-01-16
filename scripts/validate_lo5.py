"""Validate LO5 evidence outputs and integrity checks."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Sequence

REQUIRED_DOCS = (
    Path("docs/lo5/README.md"),
    Path("docs/lo5/results_summary.md"),
    Path("docs/lo5/results_log.md"),
    Path("docs/lo5/review_criteria.md"),
    Path("docs/lo5/review_scope.md"),
    Path("docs/lo5/review_report.md"),
    Path("docs/lo5/ci_pipeline_design.md"),
    Path("docs/lo5/testing_in_ci.md"),
    Path("docs/lo5/pipeline_expected_behavior.md"),
)

REQUIRED_HEADINGS = (
    "# LO5 Results Summary",
    "## Reproducibility and Integrity Checks",
    "## LO5.1 Review criteria and findings",
    "## LO5.2 CI pipeline design summary",
    "## LO5.3 Automated testing in CI",
    "## LO5.4 Expected pipeline behavior examples",
    "## Evaluation of adequacy and limitations",
)

REQUIRED_FINDING_FIELDS = {
    "id",
    "severity",
    "title",
    "description",
    "file",
    "line",
    "rationale",
    "recommendation",
}


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    return parser.parse_args()


def _require_files(paths: Sequence[Path]) -> List[str]:
    """Ensure required files exist."""

    errors: List[str] = []
    for path in paths:
        if not path.exists():
            errors.append(f"Missing required file: {path}")
    return errors


def _validate_headings(summary_path: Path) -> List[str]:
    """Validate required headings in the summary."""

    errors: List[str] = []
    content = summary_path.read_text(encoding="utf-8")
    for heading in REQUIRED_HEADINGS:
        if heading not in content:
            errors.append(f"Missing heading in summary: {heading}")
    return errors


def _validate_summary_lo3_diff(summary_path: Path) -> List[str]:
    """Validate the LO3 diff result is reported in the summary."""

    errors: List[str] = []
    content = summary_path.read_text(encoding="utf-8")
    if "LO3 diff check:" not in content:
        errors.append("Summary missing LO3 diff check result line.")
    if "LO3 diff check: empty" not in content:
        errors.append("Summary missing LO3 diff check result value.")
    return errors


def _validate_review_findings(artifacts_dir: Path) -> List[str]:
    """Validate the review findings JSON structure."""

    errors: List[str] = []
    findings_path = artifacts_dir / "review_findings.json"
    if not findings_path.exists():
        return [f"Missing review findings JSON: {findings_path}"]
    try:
        payload = json.loads(findings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"Invalid JSON in review findings: {exc}"]
    if not isinstance(payload, list):
        return ["Review findings JSON must be an array."]
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            errors.append(f"Finding {index} is not an object.")
            continue
        missing = REQUIRED_FINDING_FIELDS - set(item.keys())
        if missing:
            errors.append(
                f"Finding {index} missing fields: {', '.join(sorted(missing))}"
            )
    return errors


def _validate_results_log(log_path: Path) -> List[str]:
    """Ensure results log contains required integrity entries."""

    errors: List[str] = []
    content = log_path.read_text(encoding="utf-8")
    if "git commit" not in content:
        errors.append("Results log missing git commit entry.")
    if "git diff --name-only -- docs/lo3" not in content:
        errors.append("Results log missing LO3 diff entry.")
    if "LO3 diff check: empty" not in content:
        errors.append("Results log missing empty LO3 diff check result.")
    return errors


def _validate_lo3_diff_clean() -> List[str]:
    """Ensure LO3 artifacts are untouched by verifying git diff output."""

    result = subprocess.run(
        ["git", "diff", "--name-only", "--", "docs/lo3"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ["Failed to run git diff for docs/lo3."]
    if result.stdout.strip():
        return ["docs/lo3 has uncommitted changes."]
    return []


def main() -> int:
    """CLI entry point."""

    args = parse_args()
    errors: List[str] = []
    errors.extend(_require_files(REQUIRED_DOCS))
    if args.summary.exists():
        errors.extend(_validate_headings(args.summary))
        errors.extend(_validate_summary_lo3_diff(args.summary))
    if args.log.exists():
        errors.extend(_validate_results_log(args.log))
    errors.extend(_validate_review_findings(args.artifacts))
    errors.extend(_validate_lo3_diff_clean())
    if errors:
        for error in errors:
            print(f"[LO5 VALIDATION ERROR] {error}")
        return 1
    print("LO5 validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
