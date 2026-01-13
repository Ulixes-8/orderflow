#!/usr/bin/env python3
"""LO3: Model-based testing coverage computation."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from orderflow.testing_helpers import make_test_service
from orderflow.validation import ORDER_ALREADY_FULFILLED, ORDER_NOT_FOUND, UNAUTHORIZED


@dataclass(frozen=True)
class Args:
    """Command line arguments."""

    out: Path


def parse_args() -> Args:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description="Compute LO3 model coverage.")
    parser.add_argument("--out", type=Path, required=True)
    ns = parser.parse_args()
    return Args(out=ns.out)


def _utc_now() -> str:
    """Return UTC timestamp in ISO 8601 format."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def main() -> int:
    """Execute model-based sequences and emit coverage summary."""

    args = parse_args()

    service = make_test_service()
    mobile = "+15551234567"
    message = "ORDER COFFEE=1"

    states_defined = ["S0", "S1", "S2"]
    transitions_defined = [
        "place:S0->S1",
        "show:S1->S1",
        "list:S1->S1",
        "fulfill_auth_ok:S1->S2",
        "fulfill_auth_bad:S1->S1",
        "fulfill_on_fulfilled:S2->S2",
        "show_missing:S0->S0",
    ]

    states_visited: set[str] = set()
    transitions_visited: set[str] = set()

    states_visited.add("S0")

    missing = service.show_order("ORD-FFFFFFFF")
    if not missing.get("ok") and missing.get("error", {}).get("code") == ORDER_NOT_FOUND:
        transitions_visited.add("show_missing:S0->S0")

    placed = service.place_order(mobile, message)
    order_id = str(placed.get("data", {}).get("order_id"))
    states_visited.add("S1")
    transitions_visited.add("place:S0->S1")

    shown = service.show_order(order_id)
    if shown.get("ok"):
        transitions_visited.add("show:S1->S1")

    listed = service.list_outstanding()
    if listed.get("ok"):
        transitions_visited.add("list:S1->S1")

    bad_fulfill = service.fulfill_order(order_id, "000000")
    if not bad_fulfill.get("ok") and bad_fulfill.get("error", {}).get("code") == UNAUTHORIZED:
        transitions_visited.add("fulfill_auth_bad:S1->S1")

    good_fulfill = service.fulfill_order(order_id, "123456")
    if good_fulfill.get("ok"):
        states_visited.add("S2")
        transitions_visited.add("fulfill_auth_ok:S1->S2")

    second_fulfill = service.fulfill_order(order_id, "123456")
    if not second_fulfill.get("ok") and second_fulfill.get("error", {}).get("code") == ORDER_ALREADY_FULFILLED:
        transitions_visited.add("fulfill_on_fulfilled:S2->S2")

    state_coverage = {
        "visited": len(states_visited),
        "total": len(states_defined),
        "percent": round((len(states_visited) / len(states_defined)) * 100, 2),
    }
    transition_coverage = {
        "visited": len(transitions_visited),
        "total": len(transitions_defined),
        "percent": round((len(transitions_visited) / len(transitions_defined)) * 100, 2),
    }

    payload = {
        "generated_at": _utc_now(),
        "states_defined": states_defined,
        "transitions_defined": transitions_defined,
        "states_visited": sorted(states_visited),
        "transitions_visited": sorted(transitions_visited),
        "state_coverage": state_coverage,
        "transition_coverage": transition_coverage,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
