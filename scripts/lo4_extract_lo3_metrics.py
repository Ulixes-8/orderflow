"""Extract LO3 metrics into LO4 artifact summaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", required=True, help="Path to LO3 metrics.json.")
    parser.add_argument(
        "--error-codes",
        required=True,
        help="Path to LO3 error_codes_exercised.json.",
    )
    parser.add_argument("--coverage-output", required=True, help="Output path.")
    parser.add_argument("--failure-output", required=True, help="Output path.")
    return parser


def _load_json(path: Path) -> Dict[str, Any]:
    """Load JSON from disk."""

    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    """CLI entry point."""

    parser = _build_parser()
    args = parser.parse_args()

    metrics_path = Path(args.metrics)
    error_codes_path = Path(args.error_codes)
    metrics = _load_json(metrics_path)
    error_codes = json.loads(error_codes_path.read_text(encoding="utf-8"))

    coverage_payload = {
        "source": {
            "metrics_path": str(metrics_path),
            "generated_at": metrics.get("generated_at"),
        },
        "requirements_coverage": metrics.get("requirements_coverage", {}),
        "structural_coverage": metrics.get("structural_coverage", {}),
        "combinatorial": metrics.get("combinatorial", {}),
        "model": metrics.get("model", {}),
    }

    failure_payload = {
        "source": {
            "metrics_path": str(metrics_path),
            "error_codes_path": str(error_codes_path),
            "generated_at": metrics.get("generated_at"),
        },
        "error_codes_exercised": sorted(error_codes),
    }

    coverage_output = Path(args.coverage_output)
    coverage_output.parent.mkdir(parents=True, exist_ok=True)
    coverage_output.write_text(
        json.dumps(coverage_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    failure_output = Path(args.failure_output)
    failure_output.parent.mkdir(parents=True, exist_ok=True)
    failure_output.write_text(
        json.dumps(failure_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
