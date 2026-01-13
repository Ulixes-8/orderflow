#!/usr/bin/env python3
"""LO3: Extract planned-vs-implemented status (stub).

Intended behavior:
- Read docs/lo2/test_inventory.csv
- Discover implemented tests (pytest collection and/or name patterns)
- Emit docs/lo3/artifacts/plan_status.json suitable for implemented_vs_planned.md
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Args:
    inventory: Path
    out: Path


def parse_args() -> Args:
    parser = argparse.ArgumentParser(description="Extract LO3 plan status.")
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    ns = parser.parse_args()
    return Args(inventory=ns.inventory, out=ns.out)


def main() -> int:
    _ = parse_args()
    raise NotImplementedError("Stub: implement via Codex prompt.")


if __name__ == "__main__":
    raise SystemExit(main())
