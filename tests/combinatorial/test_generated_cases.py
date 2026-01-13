"""Run generated combinatorial cases against the CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import parse_json_stdout, run_cli


@pytest.mark.combinatorial
def test_generated_combinatorial_cases(tmp_path: Path, artifact_collector) -> None:
    """Execute generated combinatorial cases via the CLI place command."""

    repo_root = Path(__file__).resolve().parents[2]
    cases_path = repo_root / "docs" / "lo3" / "artifacts" / "combinatorial_cases.json"
    if not cases_path.exists():
        generator = repo_root / "scripts" / "lo3_combinatorial_generate.py"
        coverage_path = repo_root / "docs" / "lo3" / "artifacts" / "combinatorial_coverage.json"
        subprocess.run(
            [
                sys.executable,
                str(generator),
                "--out",
                str(coverage_path),
                "--cases-out",
                str(cases_path),
            ],
            check=True,
        )

    cases_payload = json.loads(cases_path.read_text(encoding="utf-8"))
    cases = cases_payload["cases"]

    db_path = tmp_path / "orders.db"
    env = {
        "ORDERFLOW_DB_PATH": str(db_path),
        "ORDERFLOW_AUTH_CODE": "123456",
    }

    for case in cases:
        code, stdout, _ = run_cli(
            [
                "place",
                "--mobile",
                case["mobile"],
                "--message",
                case["message"],
            ],
            cwd=Path.cwd(),
            env=env,
        )
        payload = parse_json_stdout(stdout)
        if case["expected_ok"]:
            assert code == 0
            assert payload["ok"] is True
        else:
            assert code == 2
            assert payload["ok"] is False
            error_code = payload["error"]["code"]
            artifact_collector.record_error_code(error_code)
            assert error_code == case["expected_error_code"]
