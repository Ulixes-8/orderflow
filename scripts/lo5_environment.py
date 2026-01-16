"""Collect environment metadata for LO5 evidence."""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class EnvironmentSnapshot:
    """Structured metadata about the runtime environment."""

    timestamp_utc: str
    os: str
    os_release: str
    python_version: str
    python_implementation: str
    cpu_count: int
    cpu_architecture: str
    ram_bytes: Optional[int]


def _read_total_ram_bytes() -> Optional[int]:
    """Best-effort retrieval of total RAM in bytes."""

    if hasattr(os, "sysconf"):
        page_size = os.sysconf("SC_PAGE_SIZE")
        page_count = os.sysconf("SC_PHYS_PAGES")
        if isinstance(page_size, int) and isinstance(page_count, int):
            return page_size * page_count
    return None


def collect_environment() -> EnvironmentSnapshot:
    """Collect a snapshot of environment details for auditing."""

    timestamp_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return EnvironmentSnapshot(
        timestamp_utc=timestamp_utc,
        os=platform.system(),
        os_release=platform.release(),
        python_version=platform.python_version(),
        python_implementation=platform.python_implementation(),
        cpu_count=os.cpu_count() or 0,
        cpu_architecture=platform.machine(),
        ram_bytes=_read_total_ram_bytes(),
    )


def _serialize(snapshot: EnvironmentSnapshot) -> Dict[str, Any]:
    """Serialize the snapshot for JSON output."""

    return asdict(snapshot)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to write the environment JSON snapshot.",
    )
    return parser.parse_args()


def main() -> int:
    """CLI entry point."""

    args = parse_args()
    snapshot = collect_environment()
    payload = _serialize(snapshot)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
