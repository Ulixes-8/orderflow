"""Run automated review checks for LO5.1."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

SQL_KEYWORDS = ("select", "insert", "update", "delete", "with", "pragma")
REVIEW_SCOPE = (
    Path("src/orderflow/service.py"),
    Path("src/orderflow/store/sqlite.py"),
    Path("src/orderflow/cli.py"),
)


@dataclass(frozen=True)
class ReviewFinding:
    """Structured finding emitted by LO5 review checks."""

    id: str
    severity: str
    title: str
    description: str
    file: str
    line: int
    rationale: str
    recommendation: str


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/lo5/artifacts/review_findings.json"),
        help="Path to write review findings JSON.",
    )
    return parser.parse_args()


def _load_lines(path: Path) -> List[str]:
    """Read file contents as a list of lines."""

    return path.read_text(encoding="utf-8").splitlines()


def _contains_sql(text: str) -> bool:
    """Heuristic SQL detection."""

    lowered = text.lower()
    return any(keyword in lowered for keyword in SQL_KEYWORDS)


def _is_sql_string_formatting(line: str) -> bool:
    """Detect SQL formatting patterns in a single line."""

    if not _contains_sql(line):
        return False
    if "f\"" in line or "f'" in line:
        return True
    if ".format(" in line:
        return True
    if "%" in line and ("select" in line.lower() or "insert" in line.lower()):
        return True
    return False


def _iter_findings_for_sql(path: Path, lines: Sequence[str]) -> Iterable[ReviewFinding]:
    """Detect risky SQL string formatting patterns."""

    for idx, line in enumerate(lines, start=1):
        if _is_sql_string_formatting(line):
            yield ReviewFinding(
                id=f"SQL_FMT_{path.name}_{idx}",
                severity="P1",
                title="Potential non-parameterized SQL formatting",
                description=(
                    "Detected SQL-like string formatting that may bypass bound "
                    "parameters."
                ),
                file=str(path),
                line=idx,
                rationale=(
                    "String interpolation in SQL statements can introduce "
                    "injection risks and complicate query auditing."
                ),
                recommendation=(
                    "Use parameterized SQL with bound arguments instead of "
                    "string formatting."
                ),
            )


def _iter_findings_for_stdout(path: Path, lines: Sequence[str]) -> Iterable[ReviewFinding]:
    """Detect print statements that may contaminate stdout."""

    if path.name not in {"service.py", "sqlite.py", "cli.py"}:
        return

    for idx, line in enumerate(lines, start=1):
        if "print(" not in line:
            continue
        if path.name == "cli.py":
            if re.search(r"print\(.+json", line, re.IGNORECASE):
                continue
            if re.search(r"print\(.+result", line, re.IGNORECASE):
                continue
        yield ReviewFinding(
            id=f"STDOUT_{path.name}_{idx}",
            severity="P2",
            title="Potential stdout contamination",
            description="Direct print may emit diagnostics to stdout.",
            file=str(path),
            line=idx,
            rationale=(
                "Contract JSON output must remain deterministic and free of "
                "diagnostics to avoid breaking consumers."
            ),
            recommendation=(
                "Route diagnostics to stderr or a logger and keep stdout "
                "strictly for contract output."
            ),
        )


def _iter_findings_for_seams(path: Path, lines: Sequence[str]) -> Iterable[ReviewFinding]:
    """Identify candidate fault-injection seams."""

    contents = "\n".join(lines)
    if path.name in {"service.py", "sqlite.py"} and "DATABASE_ERROR" not in contents:
        yield ReviewFinding(
            id=f"SEAM_DB_{path.name}",
            severity="P2",
            title="Missing explicit DATABASE_ERROR seam",
            description=(
                "No explicit injection seam was detected for database failure "
                "simulation."
            ),
            file=str(path),
            line=1,
            rationale=(
                "Failing to simulate database errors can leave critical error "
                "paths untested."
            ),
            recommendation=(
                "Add a dependency injection point or adapter that allows tests "
                "to trigger DATABASE_ERROR conditions."
            ),
        )
    if path.name == "cli.py" and "INTERNAL_ERROR" not in contents:
        yield ReviewFinding(
            id="SEAM_INTERNAL_cli",
            severity="P2",
            title="Missing explicit INTERNAL_ERROR seam",
            description=(
                "No explicit injection seam was detected for internal error "
                "simulation."
            ),
            file=str(path),
            line=1,
            rationale=(
                "Internal error paths are difficult to test without a "
                "controllable seam, risking regressions."
            ),
            recommendation=(
                "Provide a deterministic injection hook to simulate "
                "INTERNAL_ERROR conditions during tests."
            ),
        )


def collect_findings(paths: Sequence[Path]) -> List[ReviewFinding]:
    """Collect all findings across the review scope."""

    findings: List[ReviewFinding] = []
    for path in paths:
        if not path.exists():
            findings.append(
                ReviewFinding(
                    id=f"SCOPE_MISSING_{path.name}",
                    severity="P0",
                    title="Review scope file missing",
                    description="A scoped file does not exist in the repository.",
                    file=str(path),
                    line=0,
                    rationale=(
                        "The review scope must remain stable for auditability. "
                        "A missing file indicates a critical mismatch."
                    ),
                    recommendation="Restore the missing file or update scope.",
                )
            )
            continue
        lines = _load_lines(path)
        findings.extend(_iter_findings_for_sql(path, lines))
        findings.extend(_iter_findings_for_stdout(path, lines))
        findings.extend(_iter_findings_for_seams(path, lines))
    return findings


def write_findings(findings: Iterable[ReviewFinding], output: Path) -> None:
    """Write findings to the output JSON path."""

    output.parent.mkdir(parents=True, exist_ok=True)
    payload = [asdict(finding) for finding in findings]
    with output.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main() -> int:
    """CLI entry point."""

    args = parse_args()
    findings = collect_findings(REVIEW_SCOPE)
    write_findings(findings, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
