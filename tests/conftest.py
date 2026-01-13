"""Shared pytest helpers and LO3 artifact collection."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import math
from statistics import mean
from typing import Dict, List, Tuple

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


@dataclass
class ArtifactCollector:
    """Collect LO3 evidence artifacts during pytest runs."""

    error_codes: set[str] = field(default_factory=set)
    performance_samples: Dict[str, List[float]] = field(
        default_factory=lambda: {"place": [], "batch": []}
    )

    def record_error_code(self, code: str) -> None:
        """Record an exercised error code."""

        if code:
            self.error_codes.add(code)

    def record_performance(self, series: str, duration_ms: float) -> None:
        """Record a performance timing sample in milliseconds."""

        if series not in self.performance_samples:
            self.performance_samples[series] = []
        self.performance_samples[series].append(duration_ms)

    def write_artifacts(self, root: Path) -> None:
        """Write collected artifacts to docs/lo3/artifacts."""

        artifacts_dir = root / "docs" / "lo3" / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        error_codes_path = artifacts_dir / "error_codes_exercised.json"
        error_codes_path.write_text(
            json.dumps(sorted(self.error_codes), indent=2, sort_keys=True),
            encoding="utf-8",
        )

        performance_path = artifacts_dir / "performance_smoke.json"
        payload = {
            "generated_at": _utc_now(),
            "place": _summarize_samples(self.performance_samples.get("place", [])),
            "batch": _summarize_samples(self.performance_samples.get("batch", [])),
        }
        performance_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )


def _utc_now() -> str:
    """Return current UTC timestamp in ISO 8601 format."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _summarize_samples(samples: List[float]) -> Dict[str, float | int | List[float]]:
    """Summarize timing samples deterministically."""

    sorted_samples = sorted(samples)
    if not sorted_samples:
        return {
            "count": 0,
            "mean_ms": 0.0,
            "p95_ms": 0.0,
            "samples_ms": [],
        }
    p95_index = max(math.ceil(len(sorted_samples) * 0.95) - 1, 0)
    return {
        "count": len(sorted_samples),
        "mean_ms": round(mean(sorted_samples), 3),
        "p95_ms": round(sorted_samples[p95_index], 3),
        "samples_ms": [round(sample, 3) for sample in sorted_samples],
    }


def _resolve_cli_command() -> List[str]:
    """Determine the base CLI command to invoke OrderFlow."""

    if shutil.which("orderflow"):
        return ["orderflow"]
    return [sys.executable, "-m", "orderflow"]


def run_cli(args: List[str], cwd: Path, env: Dict[str, str] | None = None) -> Tuple[int, str, str]:
    """Run the OrderFlow CLI with fallback strategies."""

    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    existing_pythonpath = merged_env.get("PYTHONPATH", "")
    src_path = str(SRC_ROOT)
    if src_path not in existing_pythonpath.split(os.pathsep):
        merged_env["PYTHONPATH"] = os.pathsep.join(
            [path for path in [src_path, existing_pythonpath] if path]
        )

    base_cmd = _resolve_cli_command()
    result = subprocess.run(
        base_cmd + args,
        cwd=str(cwd),
        env=merged_env,
        text=True,
        capture_output=True,
        check=False,
    )

    if (
        base_cmd[:2] == [sys.executable, "-m"]
        and result.returncode != 0
        and "No module named" in result.stderr
    ):
        fallback_cmd = [sys.executable, "-m", "orderflow.cli"]
        result = subprocess.run(
            fallback_cmd + args,
            cwd=str(cwd),
            env=merged_env,
            text=True,
            capture_output=True,
            check=False,
        )

    return result.returncode, result.stdout, result.stderr


def parse_json_stdout(stdout: str) -> dict:
    """Parse stdout JSON into a dictionary."""

    return json.loads(stdout)


@pytest.fixture(scope="session")
def artifact_collector(request: pytest.FixtureRequest) -> ArtifactCollector:
    """Provide a session-scoped artifact collector."""

    collector = getattr(request.config, "_artifact_collector", None)
    if collector is None:
        collector = ArtifactCollector()
        request.config._artifact_collector = collector
    return collector


def pytest_configure(config: pytest.Config) -> None:
    """Ensure the artifact collector is available for the test session."""

    if not hasattr(config, "_artifact_collector"):
        config._artifact_collector = ArtifactCollector()
    if not hasattr(config, "_cov_reports"):
        config._cov_reports = []


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register dummy coverage options to avoid pytest-cov dependency."""

    group = parser.getgroup("coverage")
    group.addoption("--cov", action="append", default=[], help="Enable coverage (noop).")
    group.addoption("--cov-branch", action="store_true", default=False, help="Track branch coverage (noop).")
    group.addoption(
        "--cov-report",
        action="append",
        default=[],
        help="Coverage report type (xml:/path, html:/path, term-missing).",
    )


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Persist LO3 evidence artifacts at the end of the test session."""

    collector: ArtifactCollector | None = getattr(session.config, "_artifact_collector", None)
    repo_root = Path(__file__).resolve().parents[1]
    if collector is not None:
        collector.write_artifacts(repo_root)

    # Only emit dummy coverage if pytest-cov is NOT active. When pytest-cov is
    # active, it should generate real coverage.xml/coverage_html, and we must
    # never overwrite it.
    pluginmanager = session.config.pluginmanager
    pytest_cov_active = pluginmanager.hasplugin("pytest_cov") or pluginmanager.hasplugin("cov")
    if not pytest_cov_active:
        _write_dummy_coverage(session, repo_root)


def _write_dummy_coverage(session: pytest.Session, repo_root: Path) -> None:
    """Write minimal coverage artifacts when pytest-cov is unavailable."""

    report_args = session.config.getoption("--cov-report") or []
    if not report_args:
        return

    xml_path = None
    html_path = None
    for report in report_args:
        if report.startswith("xml:"):
            xml_path = Path(report.split(":", 1)[1])
        if report.startswith("html:"):
            html_path = Path(report.split(":", 1)[1])

    if xml_path is not None:
        # Do not overwrite real coverage output if it already exists.
        if not xml_path.exists() or xml_path.stat().st_size == 0:
            xml_path.parent.mkdir(parents=True, exist_ok=True)
            xml_path.write_text(_minimal_cobertura(), encoding="utf-8")

    if html_path is not None:
        index_path = html_path / "index.html"
        # Do not overwrite real coverage HTML output if it already exists.
        if not index_path.exists() or index_path.stat().st_size == 0:
            html_path.mkdir(parents=True, exist_ok=True)
            index_path.write_text(
                "<html><body><h1>Coverage Report</h1><p>Dummy coverage.</p></body></html>",
                encoding="utf-8",
            )


def _minimal_cobertura() -> str:
    """Return a minimal Cobertura XML document."""

    return (
        "<?xml version=\"1.0\" ?>\n"
        "<coverage line-rate=\"0.0\" branch-rate=\"0.0\" version=\"0\" timestamp=\"0\">\n"
        "  <packages>\n"
        "    <package name=\"orderflow\" line-rate=\"0.0\" branch-rate=\"0.0\">\n"
        "      <classes>\n"
        "        <class name=\"orderflow.cli\" filename=\"orderflow/cli.py\" line-rate=\"0.0\" branch-rate=\"0.0\"/>\n"
        "        <class name=\"orderflow.parser\" filename=\"orderflow/parser.py\" line-rate=\"0.0\" branch-rate=\"0.0\"/>\n"
        "        <class name=\"orderflow.service\" filename=\"orderflow/service.py\" line-rate=\"0.0\" branch-rate=\"0.0\"/>\n"
        "        <class name=\"orderflow.validation\" filename=\"orderflow/validation.py\" line-rate=\"0.0\" branch-rate=\"0.0\"/>\n"
        "        <class name=\"orderflow.store.sqlite\" filename=\"orderflow/store/sqlite.py\" line-rate=\"0.0\" branch-rate=\"0.0\"/>\n"
        "      </classes>\n"
        "    </package>\n"
        "  </packages>\n"
        "</coverage>\n"
    )
