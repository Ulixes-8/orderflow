"""Collect runtime environment details for LO4 evidence."""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any, Dict, Optional


def _read_cpu_model() -> Optional[str]:
    """Return the CPU model name when available."""

    cpuinfo_path = Path("/proc/cpuinfo")
    if cpuinfo_path.exists():
        for line in cpuinfo_path.read_text(encoding="utf-8").splitlines():
            if line.lower().startswith("model name"):
                return line.split(":", 1)[1].strip()
    processor = platform.processor().strip()
    return processor or None


def _read_memory_bytes() -> Optional[int]:
    """Return total system memory in bytes when available."""

    meminfo_path = Path("/proc/meminfo")
    if meminfo_path.exists():
        for line in meminfo_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                parts = line.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    return int(parts[1]) * 1024
    try:
        import psutil  # type: ignore

        return int(psutil.virtual_memory().total)
    except ImportError:
        return None


def collect_environment() -> Dict[str, Any]:
    """Collect platform and interpreter details for LO4 evidence."""

    return {
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
        },
        "python": {
            "version": sys.version.replace("\n", " "),
            "executable": sys.executable,
        },
        "hardware": {
            "cpu_model": _read_cpu_model(),
            "cpu_count": os.cpu_count(),
            "memory_bytes": _read_memory_bytes(),
        },
    }


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="Path to environment.json.")
    return parser


def main() -> None:
    """CLI entry point."""

    parser = _build_parser()
    args = parser.parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = collect_environment()
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
