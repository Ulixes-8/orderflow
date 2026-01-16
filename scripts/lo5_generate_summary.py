"""Generate LO5 results summary from evidence artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


@dataclass(frozen=True)
class EnvironmentInfo:
    """Environment metadata loaded from JSON."""

    os: str
    os_release: str
    python_version: str
    python_implementation: str
    cpu_count: int
    cpu_architecture: str
    ram_bytes: int | None


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", type=Path, required=True)
    parser.add_argument("--review-findings", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--git-commit", type=str, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    return parser.parse_args()


def _load_environment(path: Path) -> EnvironmentInfo:
    """Load environment info from JSON."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    return EnvironmentInfo(
        os=payload.get("os", "unknown"),
        os_release=payload.get("os_release", "unknown"),
        python_version=payload.get("python_version", "unknown"),
        python_implementation=payload.get("python_implementation", "unknown"),
        cpu_count=int(payload.get("cpu_count", 0)),
        cpu_architecture=payload.get("cpu_architecture", "unknown"),
        ram_bytes=payload.get("ram_bytes"),
    )


def _load_findings(path: Path) -> List[Dict[str, str]]:
    """Load review findings JSON."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Review findings JSON must be a list.")
    return payload


def _summarize_findings(findings: Sequence[Dict[str, str]]) -> Dict[str, int]:
    """Count findings by severity."""

    counts: Dict[str, int] = {"P0": 0, "P1": 0, "P2": 0}
    for finding in findings:
        severity = str(finding.get("severity", "P2"))
        counts[severity] = counts.get(severity, 0) + 1
    return counts


def _summarize_findings_by_file(findings: Sequence[Dict[str, str]]) -> Dict[str, int]:
    """Count findings by file path."""

    counts: Dict[str, int] = {}
    for finding in findings:
        file_name = str(finding.get("file", "unknown"))
        counts[file_name] = counts.get(file_name, 0) + 1
    return counts


def _format_ram(ram_bytes: int | None) -> str:
    """Format RAM information for display."""

    if ram_bytes is None:
        return "unknown"
    gigabytes = ram_bytes / (1024**3)
    return f"{gigabytes:.2f} GB"


def _extract_lo3_diff_statement(log_path: Path) -> str:
    """Extract the most recent LO3 diff result statement from the log."""

    lines = log_path.read_text(encoding="utf-8").splitlines()
    result_lines = [line for line in lines if "LO3 diff check:" in line]
    if result_lines:
        latest = result_lines[-1].strip()
        return latest.split("LO3 diff check:", 1)[-1].strip() or "unknown"
    command_lines = [
        line for line in lines if "git diff --name-only -- docs/lo3" in line
    ]
    if command_lines:
        return "unknown (see log for command output)"
    return "unknown (no entry recorded)"


def _render_findings_table(findings: Iterable[Dict[str, str]]) -> str:
    """Render a Markdown table for findings."""

    rows = [
        "| ID | Severity | Title | File | Line | Recommendation |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for finding in findings:
        line_value = finding.get("line", "")
        line_display = "n/a" if str(line_value) == "0" else str(line_value)
        rows.append(
            "| {id} | {severity} | {title} | {file} | {line} | {rec} |".format(
                id=finding.get("id", ""),
                severity=finding.get("severity", ""),
                title=finding.get("title", ""),
                file=finding.get("file", ""),
                line=line_display,
                rec=finding.get("recommendation", ""),
            )
        )
    return "\n".join(rows)


def _render_issue_examples() -> str:
    """Render issue-to-detector examples summary."""

    examples = [
        "- LO artifact drift detected by LO validators (Stage 0).",
        "- CLI contract regression detected by contract tests (Stage 2).",
        "- Non-parameterized SQL detected by LO5 review checks (Stage 0).",
        "- Missing failure-mode mapping flagged in LO5 review checks (Stage 0).",
        "- Diagnostics contaminating stdout detected by review checks or contract tests.",
        "- Unit regression detected by pytest (Stage 1).",
        "- Integration regression detected by pytest integration tests (Stage 1).",
        "- Performance regression detected by nightly LO4 benchmark runner.",
    ]
    return "\n".join(examples)


def generate_summary(
    environment: EnvironmentInfo,
    findings: Sequence[Dict[str, str]],
    log_path: Path,
    git_commit: str,
    run_dir: Path,
) -> str:
    """Generate the markdown summary content."""

    counts = _summarize_findings(findings)
    total_findings = sum(counts.values())
    file_counts = _summarize_findings_by_file(findings)
    file_breakdown = ", ".join(
        f"{file_name}={count}" for file_name, count in sorted(file_counts.items())
    )
    lo3_diff_statement = _extract_lo3_diff_statement(log_path)
    findings_table = _render_findings_table(findings)
    issue_examples = _render_issue_examples()

    return "\n".join(
        [
            "# LO5 Results Summary",
            "## Reproducibility and Integrity Checks",
            f"- Git commit: `{git_commit}`",
            (
                "- OS/Python/CPU/Cores/RAM: "
                f"{environment.os} {environment.os_release} / "
                f"{environment.python_implementation} {environment.python_version} / "
                f"{environment.cpu_architecture} / "
                f"{environment.cpu_count} cores / "
                f"{_format_ram(environment.ram_bytes)}"
            ),
            f"- Run directory: `{run_dir.as_posix()}`",
            f"- LO3 diff check: {lo3_diff_statement}",
            "## LO5.1 Review criteria and findings",
            (
                "- Findings by severity: "
                f"P0={counts.get('P0', 0)}, "
                f"P1={counts.get('P1', 0)}, "
                f"P2={counts.get('P2', 0)}"
            ),
            f"- Total findings: {total_findings}",
            f"- Findings by file: {file_breakdown}",
            findings_table,
            "## LO5.2 CI pipeline design summary",
            (
                "Design only; not implemented. See "
                "`docs/lo5/ci_pipeline_design.md` for the proposed stages, "
                "triggers, and artifacts."
            ),
            "## LO5.3 Automated testing in CI",
            (
                "Merge-gating vs. nightly responsibilities are defined in "
                "`docs/lo5/testing_in_ci.md`. Gating focuses on validators "
                "and fast pytest execution; nightly includes LO4 benchmarks."
            ),
            "## LO5.4 Expected pipeline behavior examples",
            (
                "Examples derived from "
                "`docs/lo5/pipeline_expected_behavior.md`:"
            ),
            issue_examples,
            "## Evaluation of adequacy and limitations",
            (
                "The LO5 review and CI design reduce risk by codifying review "
                "criteria, automated checks, and evidence retention. They are "
                "proxies for correctness and do not guarantee the absence of "
                "defects, especially for unmodeled failures or environment-"
                "specific performance behavior."
            ),
        ]
    )


def main() -> int:
    """CLI entry point."""

    args = parse_args()
    environment = _load_environment(args.environment)
    findings = _load_findings(args.review_findings)
    summary = generate_summary(
        environment=environment,
        findings=findings,
        log_path=args.log,
        git_commit=args.git_commit,
        run_dir=args.run_dir,
    )
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(summary + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
