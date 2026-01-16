"""Run LO4 performance benchmarks for place and batch commands."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.lo4_stats import BootstrapConfig, summarize_samples, summarize_throughput

SRC_ROOT = REPO_ROOT / "src"
CATALOGUE_PATH = REPO_ROOT / "data" / "catalogue.json"

DEFAULT_PLACE_SAMPLES = 60
DEFAULT_BATCH_SAMPLES = 60
DEFAULT_WARMUP = 5
DEFAULT_BATCH_LINES = 20


def _resolve_cli_command() -> List[str]:
    """Determine the base CLI command to invoke OrderFlow."""

    if shutil.which("orderflow"):
        return ["orderflow"]
    return [sys.executable, "-m", "orderflow"]


def _run_cli(args: List[str], env: Dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Run the OrderFlow CLI and return the completed process."""

    merged_env = os.environ.copy()
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
        cwd=str(REPO_ROOT),
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
            cwd=str(REPO_ROOT),
            env=merged_env,
            text=True,
            capture_output=True,
            check=False,
        )
    return result


def _measure_command(args: List[str], db_path: Path) -> float:
    """Measure the total elapsed time of a CLI invocation."""

    env = {"ORDERFLOW_DB_PATH": str(db_path)}
    start = time.perf_counter()
    result = _run_cli(args, env)
    end = time.perf_counter()
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(args)}\nstdout={result.stdout}\nstderr={result.stderr}"
        )
    return (end - start) * 1000.0


def _place_args(sku: str) -> List[str]:
    """Return the CLI args for a typical place command."""

    return [
        "place",
        "--mobile",
        "+447700900123",
        "--message",
        f"ORDER {sku}=1",
    ]


def _build_batch_input(path: Path, lines: int, sku: str) -> None:
    """Write a batch input file with valid lines."""

    with path.open("w", encoding="utf-8") as handle:
        for index in range(lines):
            mobile = f"+447700900{100 + index:03d}"
            handle.write(f"{mobile}|ORDER {sku}=1\n")


def _load_default_sku() -> str:
    """Load the first catalogue SKU for deterministic workload definition."""

    payload = json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))
    items = payload.get("items", [])
    if not items:
        raise RuntimeError("Catalogue contains no items to benchmark.")
    sku = str(items[0].get("sku", "")).strip().upper()
    if not sku:
        raise RuntimeError("Catalogue item missing SKU.")
    return sku


def _run_place_samples(samples: int, warmup: int, sku: str) -> List[float]:
    """Collect place timing samples."""

    measurements: List[float] = []
    for _ in range(warmup):
        with tempfile.TemporaryDirectory() as tempdir:
            db_path = Path(tempdir) / "orderflow.db"
            _measure_command(_place_args(sku), db_path)
    for _ in range(samples):
        with tempfile.TemporaryDirectory() as tempdir:
            db_path = Path(tempdir) / "orderflow.db"
            measurements.append(_measure_command(_place_args(sku), db_path))
    return measurements


def _run_batch_samples(samples: int, warmup: int, lines: int, sku: str) -> List[float]:
    """Collect batch timing samples."""

    measurements: List[float] = []
    for _ in range(warmup):
        with tempfile.TemporaryDirectory() as tempdir:
            db_path = Path(tempdir) / "orderflow.db"
            input_path = Path(tempdir) / "batch_input.txt"
            _build_batch_input(input_path, lines, sku)
            _measure_command(["batch", "--input", str(input_path)], db_path)
    for _ in range(samples):
        with tempfile.TemporaryDirectory() as tempdir:
            db_path = Path(tempdir) / "orderflow.db"
            input_path = Path(tempdir) / "batch_input.txt"
            _build_batch_input(input_path, lines, sku)
            measurements.append(_measure_command(["batch", "--input", str(input_path)], db_path))
    return measurements


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples-output", required=True, help="Path for raw samples JSON.")
    parser.add_argument("--stats-output", required=True, help="Path for stats JSON.")
    return parser


def _env_int(name: str, default: int) -> int:
    """Read an integer from environment with fallback."""

    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


def main() -> None:
    """CLI entry point."""

    parser = _build_parser()
    args = parser.parse_args()

    samples_place = _env_int("ORDERFLOW_LO4_SAMPLES_PLACE", DEFAULT_PLACE_SAMPLES)
    samples_batch = _env_int("ORDERFLOW_LO4_SAMPLES_BATCH", DEFAULT_BATCH_SAMPLES)
    warmup = _env_int("ORDERFLOW_LO4_WARMUP", DEFAULT_WARMUP)
    batch_lines = _env_int("ORDERFLOW_LO4_BATCH_LINES", DEFAULT_BATCH_LINES)

    sku = _load_default_sku()
    place_samples = _run_place_samples(samples_place, warmup, sku)
    batch_samples = _run_batch_samples(samples_batch, warmup, batch_lines, sku)

    samples_payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "catalogue_path": str(CATALOGUE_PATH),
        "place": {
            "samples_ms": [round(sample, 3) for sample in place_samples],
            "count": len(place_samples),
        },
        "batch": {
            "samples_ms": [round(sample, 3) for sample in batch_samples],
            "count": len(batch_samples),
            "lines_per_batch": batch_lines,
        },
        "workload": {
            "place": {
                "mobile": "+447700900123",
                "message": f"ORDER {sku}=1",
            },
            "batch": {"lines": batch_lines, "message": f"ORDER {sku}=1"},
        },
        "configuration": {
            "samples_place": samples_place,
            "samples_batch": samples_batch,
            "warmup": warmup,
        },
    }

    bootstrap = BootstrapConfig(resamples=2000, seed=0)
    batch_summary = summarize_samples(batch_samples, bootstrap)
    batch_summary["throughput"] = summarize_throughput(
        batch_samples,
        batch_lines,
        bootstrap,
    )

    stats_payload = {
        "generated_at": samples_payload["generated_at"],
        "place": summarize_samples(place_samples, bootstrap),
        "batch": batch_summary,
        "ci_method": "bootstrap_percentile",
        "bootstrap_resamples": bootstrap.resamples,
        "assumptions": [
            "Independent samples with identical workload per run.",
            "Warmup runs discarded.",
        ],
        "workload": samples_payload["workload"],
        "configuration": samples_payload["configuration"],
    }

    samples_output = Path(args.samples_output)
    samples_output.parent.mkdir(parents=True, exist_ok=True)
    samples_output.write_text(
        json.dumps(samples_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    stats_output = Path(args.stats_output)
    stats_output.parent.mkdir(parents=True, exist_ok=True)
    stats_output.write_text(
        json.dumps(stats_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
