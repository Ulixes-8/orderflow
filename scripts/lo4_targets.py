"""Generate LO4 target definitions from LO1 requirements."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Tuple


PLACE_REQ_ID = "R-PERF-PLACE-01"


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirements", required=True, help="Path to requirements.json.")
    parser.add_argument("--output", required=True, help="Path to targets.json.")
    return parser


def _load_json(path: Path) -> Dict[str, Any]:
    """Load JSON data from disk."""

    return json.loads(path.read_text(encoding="utf-8"))


def _extract_place_targets(acceptance: str) -> Tuple[float, float]:
    """Extract numeric place targets from requirement acceptance text."""

    matches = re.findall(r"([0-9]+)ms", acceptance)
    if len(matches) < 2:
        raise ValueError("Unable to parse place performance targets from acceptance text.")
    mean_ms = float(matches[0])
    p95_ms = float(matches[1])
    return mean_ms, p95_ms


def main() -> None:
    """CLI entry point."""

    parser = _build_parser()
    args = parser.parse_args()

    requirements_path = Path(args.requirements)
    requirements = _load_json(requirements_path)
    requirement_text = ""
    acceptance_text = ""
    for req in requirements.get("requirements", []):
        if req.get("id") == PLACE_REQ_ID:
            requirement_text = req.get("statement", "")
            acceptance_text = req.get("acceptance", "")
            break

    if not acceptance_text:
        raise ValueError(f"Requirement {PLACE_REQ_ID} not found.")

    place_mean_ms, place_p95_ms = _extract_place_targets(acceptance_text)

    payload = {
        "generated_at": requirements.get("generated_at"),
        "sources": {
            "requirements_path": str(requirements_path),
            "place_requirement_id": PLACE_REQ_ID,
        },
        "requirements_coverage": {"target_percent": 100.0},
        "structural_coverage": {
            "modules": {
                "orderflow/parser.py": {"line_rate": 0.9, "branch_rate": 0.75},
                "orderflow/validation.py": {"line_rate": 0.9, "branch_rate": 0.75},
                "orderflow/store/sqlite.py": {"line_rate": 0.8, "branch_rate": 0.7},
                "orderflow/service.py": {"line_rate": 0.65, "branch_rate": 0.5},
            },
            "notes": (
                "CLI subprocess coverage is reported but not used as a primary "
                "adequacy target."
            ),
        },
        "failure_modes": {
            "required_codes": [
                "INVALID_MOBILE",
                "MESSAGE_TOO_LONG",
                "PARSE_ERROR",
                "TOO_MANY_ITEMS",
                "UNKNOWN_ITEM",
                "INVALID_QUANTITY",
                "UNAUTHORIZED",
                "ORDER_NOT_FOUND",
                "ORDER_ALREADY_FULFILLED",
                "DATABASE_ERROR",
                "INTERNAL_ERROR",
            ],
            "notes": "Codes derived from docs/cli_contract.md.",
        },
        "performance": {
            "place": {
                "mean_ms": place_mean_ms,
                "p95_ms": place_p95_ms,
                "requirement_id": PLACE_REQ_ID,
                "requirement_text": requirement_text,
                "acceptance_text": acceptance_text,
            },
            "batch": {
                "mean_ms": 80.0,
                "p95_ms": 140.0,
                "lines_per_batch": 20,
                "motivation": (
                    "Targets set slightly above LO3 smoke baselines to be realistic "
                    "while still requiring headroom for batch processing."
                ),
            },
        },
        "measurement_quality": {
            "samples_place": 60,
            "samples_batch": 60,
            "warmup": 5,
            "ci_method": "bootstrap_percentile",
            "bootstrap_resamples": 2000,
            "assumptions": [
                "Independent samples under identical workload.",
                "Warmup samples discarded.",
            ],
        },
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
