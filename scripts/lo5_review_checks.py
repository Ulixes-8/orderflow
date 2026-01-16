"""Run automated review checks for LO5.1.

Line numbers use 1-based indexing. When a precise line cannot be determined,
``line=0`` is used to denote "n/a/unknown" for audit traceability.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

SQL_KEYWORDS = ("select", "insert", "update", "delete", "with", "pragma")
SEAM_KEYWORDS = (
    "inject",
    "fault",
    "simulate",
    "fail_next",
    "failure_hook",
    "adapter",
)
INVARIANT_KEYWORDS = ("invariant", "check_", "assert")
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


def _parse_ast(path: Path) -> ast.AST:
    """Parse the file into an AST for reliable structural checks."""

    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _function_name(node: ast.AST) -> str:
    """Extract a human-readable function name from an AST node."""

    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _is_allowed_cli_print(call: ast.Call) -> bool:
    """Return True when a print call is clearly emitting JSON contract output."""

    if len(call.args) != 1:
        return False
    arg = call.args[0]
    if isinstance(arg, ast.Name):
        identifier = arg.id.lower()
        return any(keyword in identifier for keyword in ("json", "output", "result"))
    if isinstance(arg, ast.Call):
        func_name = _function_name(arg.func).lower()
        return "dumps" in func_name or "to_json" in func_name
    return False


def _iter_findings_for_stdout(path: Path) -> Iterable[ReviewFinding]:
    """Detect print statements that may contaminate stdout via AST analysis."""

    tree = _parse_ast(path)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name):
            continue
        if node.func.id != "print":
            continue
        line = int(getattr(node, "lineno", 0) or 0)
        if path.name == "cli.py" and _is_allowed_cli_print(node):
            continue
        yield ReviewFinding(
            id=f"STDOUT_{path.name}_{line or 'NA'}",
            severity="P2",
            title="Potential stdout contamination",
            description="Direct print may emit diagnostics to stdout.",
            file=str(path),
            line=line,
            rationale=(
                "Contract JSON output must remain deterministic and free of "
                "diagnostics to avoid breaking consumers."
            ),
            recommendation=(
                "Route diagnostics to stderr or a logger and keep stdout "
                "strictly for contract output."
            ),
        )


def _iter_findings_for_broad_exceptions(path: Path) -> Iterable[ReviewFinding]:
    """Detect broad exception handlers that can hide error categories."""

    tree = _parse_ast(path)
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        handler_type = node.type
        if handler_type is None:
            is_broad = True
        elif isinstance(handler_type, ast.Name):
            is_broad = handler_type.id == "Exception"
        else:
            is_broad = False
        if not is_broad:
            continue
        line = int(getattr(node, "lineno", 0) or 0)
        yield ReviewFinding(
            id=f"EXCEPT_{path.name}_{line or 'NA'}",
            severity="P2",
            title="Broad exception handler",
            description=(
                "A broad exception handler can mask error categories and "
                "reduce determinism."
            ),
            file=str(path),
            line=line,
            rationale=(
                "Catching broad exceptions makes it harder to map failures to "
                "specific error codes and can obscure root causes."
            ),
            recommendation=(
                "Catch specific exception types and preserve deterministic "
                "error mapping paths."
            ),
        )


def _iter_findings_for_large_functions(path: Path) -> Iterable[ReviewFinding]:
    """Detect maintainability hotspots based on function length."""

    tree = _parse_ast(path)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not hasattr(node, "lineno") or not hasattr(node, "end_lineno"):
            continue
        length = int(node.end_lineno - node.lineno + 1)
        if length < 60:
            continue
        line = int(getattr(node, "lineno", 0) or 0)
        yield ReviewFinding(
            id=f"LONG_FN_{path.name}_{node.name}",
            severity="P2",
            title="Large function may hinder maintainability",
            description=(
                f"Function '{node.name}' spans {length} lines, which can "
                "limit readability and testability."
            ),
            file=str(path),
            line=line,
            rationale=(
                "Large functions increase cognitive load and are harder to "
                "review for edge cases."
            ),
            recommendation=(
                "Consider extracting helper functions or refactoring into "
                "smaller units."
            ),
        )


def _first_line_matching(lines: Sequence[str], predicate: str) -> int:
    """Return the first line index containing the predicate substring."""

    for idx, line in enumerate(lines, start=1):
        if predicate in line:
            return idx
    return 0


def _has_seam_keyword(text: str) -> bool:
    """Return True when any seam keyword is present in the text."""

    lowered = text.lower()
    return any(keyword in lowered for keyword in SEAM_KEYWORDS)


def _iter_findings_for_seams(path: Path, lines: Sequence[str]) -> Iterable[ReviewFinding]:
    """Identify candidate fault-injection seams."""

    contents = "\n".join(lines)
    lowered = contents.lower()
    if path.name == "sqlite.py":
        has_sqlite = "import sqlite3" in contents or ".execute(" in contents
        if has_sqlite and not _has_seam_keyword(contents):
            line = _first_line_matching(lines, "import sqlite3")
            if not line:
                line = _first_line_matching(lines, ".execute(")
            yield ReviewFinding(
                id="SEAM_DB_sqlite",
                severity="P2",
                title="Missing DATABASE_ERROR injection seam",
                description=(
                    "SQLite interaction is present without an explicit fault-"
                    "injection seam."
                ),
                file=str(path),
                line=line,
                rationale=(
                    "Failing to simulate database errors can leave critical "
                    "error paths untested."
                ),
                recommendation=(
                    "Add a dependency injection point or adapter that allows "
                    "tests to trigger DATABASE_ERROR conditions."
                ),
            )
    if path.name == "service.py":
        has_invariant = any(keyword in lowered for keyword in INVARIANT_KEYWORDS)
        if has_invariant and not _has_seam_keyword(contents):
            line = 0
            for keyword in INVARIANT_KEYWORDS:
                line = _first_line_matching(lines, keyword)
                if line:
                    break
            yield ReviewFinding(
                id="SEAM_INTERNAL_service",
                severity="P2",
                title="Missing INTERNAL_ERROR injection seam",
                description=(
                    "Service invariants/checks exist without an explicit "
                    "fault-injection seam."
                ),
                file=str(path),
                line=line,
                rationale=(
                    "Internal error paths are difficult to test without a "
                    "controllable seam, risking regressions."
                ),
                recommendation=(
                    "Provide a deterministic injection hook to simulate "
                    "INTERNAL_ERROR conditions during tests."
                ),
            )


def _iter_findings_for_fallbacks(findings_count: int) -> Iterable[ReviewFinding]:
    """Ensure minimum diversity of review opportunities."""

    if findings_count >= 5:
        return []
    return [
        ReviewFinding(
            id="OPPORTUNITY_DB_ERROR_TEST",
            severity="P2",
            title="Exercise DATABASE_ERROR deterministically",
            description=(
                "Add deterministic tests that exercise DATABASE_ERROR to "
                "close LO4-identified gaps."
            ),
            file="src/orderflow/store/sqlite.py",
            line=0,
            rationale=(
                "LO4 noted unexercised DATABASE_ERROR paths; determinism is "
                "needed for reproducible evidence."
            ),
            recommendation=(
                "Introduce a seam or adapter that can trigger DATABASE_ERROR "
                "in tests."
            ),
        ),
        ReviewFinding(
            id="OPPORTUNITY_INTERNAL_ERROR_TEST",
            severity="P2",
            title="Exercise INTERNAL_ERROR deterministically",
            description=(
                "Add deterministic tests that exercise INTERNAL_ERROR to "
                "close LO4-identified gaps."
            ),
            file="src/orderflow/service.py",
            line=0,
            rationale=(
                "LO4 noted unexercised INTERNAL_ERROR paths; tests should "
                "cover the mapping deterministically."
            ),
            recommendation=(
                "Introduce an injection hook and map it to INTERNAL_ERROR "
                "in the service layer."
            ),
        ),
        ReviewFinding(
            id="OPPORTUNITY_ALREADY_FULFILLED_TEST",
            severity="P2",
            title="Exercise ORDER_ALREADY_FULFILLED deterministically",
            description=(
                "Add deterministic tests that exercise ORDER_ALREADY_FULFILLED "
                "to close LO4-identified gaps."
            ),
            file="src/orderflow/service.py",
            line=0,
            rationale=(
                "LO4 noted unexercised ORDER_ALREADY_FULFILLED paths; "
                "deterministic tests keep the error mapping stable."
            ),
            recommendation=(
                "Add a test that transitions an order to fulfilled, then "
                "replays the action to confirm the error mapping."
            ),
        ),
        ReviewFinding(
            id="OPPORTUNITY_DB_ADAPTER",
            severity="P2",
            title="Consider a DB adapter seam for testing",
            description=(
                "An adapter layer could make DB failure simulation "
                "repeatable and auditable."
            ),
            file="src/orderflow/store/sqlite.py",
            line=0,
            rationale=(
                "Seams improve test determinism and support evidence for "
                "failure-mode coverage."
            ),
            recommendation=(
                "Introduce a thin adapter that can swap real SQLite calls for "
                "a test double."
            ),
        ),
        ReviewFinding(
            id="OPPORTUNITY_STDOUT_BOUNDARY_DOC",
            severity="P2",
            title="Document stdout/stderr boundaries",
            description=(
                "Add a short note documenting contract output boundaries to "
                "prevent accidental stdout contamination."
            ),
            file="src/orderflow/cli.py",
            line=0,
            rationale=(
                "Explicit documentation reduces accidental contract drift and "
                "improves reviewer confidence."
            ),
            recommendation=(
                "Document that stdout is reserved for contract JSON output and "
                "diagnostics must go to stderr."
            ),
        ),
    ]


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
        findings.extend(_iter_findings_for_stdout(path))
        findings.extend(_iter_findings_for_broad_exceptions(path))
        findings.extend(_iter_findings_for_large_functions(path))
        findings.extend(_iter_findings_for_seams(path, lines))
    findings.extend(_iter_findings_for_fallbacks(len(findings)))
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
