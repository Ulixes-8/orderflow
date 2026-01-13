#!/usr/bin/env python3
"""LO3: Generate combinatorial cases + compute coverage."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class Args:
    """Command line arguments."""

    out: Path
    cases_out: Path


def parse_args() -> Args:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description="Generate LO3 combinatorial cases.")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cases-out", type=Path, required=True)
    ns = parser.parse_args()
    return Args(out=ns.out, cases_out=ns.cases_out)


def _utc_now() -> str:
    """Return UTC timestamp in ISO 8601 format."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _build_message(message_class: str) -> Tuple[str, bool, str]:
    """Build message strings and expected results for a message class."""

    if message_class == "valid":
        return "ORDER COFFEE=1", True, ""
    if message_class == "invalid_prefix":
        return "BUY COFFEE=1", False, "PARSE_ERROR"
    if message_class == "unknown_sku":
        return "ORDER PIZZA=1", False, "UNKNOWN_ITEM"
    if message_class == "qty_zero":
        return "ORDER COFFEE=0", False, "INVALID_QUANTITY"
    if message_class == "qty_too_large":
        return "ORDER COFFEE=100", False, "INVALID_QUANTITY"
    if message_class == "too_many_items":
        items = " ".join(["COFFEE=1"] * 21)
        return f"ORDER {items}", False, "TOO_MANY_ITEMS"
    raise ValueError(f"Unknown message_class: {message_class}")


def _build_mobile(mobile_class: str) -> Tuple[str, bool, str]:
    """Build mobile strings and expected results for a mobile class."""

    if mobile_class == "valid":
        return "+15551234567", True, ""
    if mobile_class == "missing_plus":
        return "15551234567", False, "INVALID_MOBILE"
    if mobile_class == "too_short":
        return "+1234", False, "INVALID_MOBILE"
    if mobile_class == "too_long":
        return "+12345678901234567", False, "INVALID_MOBILE"
    if mobile_class == "non_digit":
        return "+12345ABCD", False, "INVALID_MOBILE"
    raise ValueError(f"Unknown mobile_class: {mobile_class}")


def _expected_result(
    mobile_class: str, message_class: str
) -> Tuple[bool, str]:
    """Derive expected ok/error based on validation precedence."""

    _, mobile_ok, mobile_error = _build_mobile(mobile_class)
    if not mobile_ok:
        return False, mobile_error
    _, message_ok, message_error = _build_message(message_class)
    if not message_ok:
        return False, message_error
    return True, ""


def _compute_category_coverage(values: list[str], seen: set[str]) -> dict[str, float | int]:
    """Compute coverage stats for a category."""

    total = len(values)
    covered = len({value for value in values if value in seen})
    percent = (covered / total) * 100 if total else 0.0
    return {"covered": covered, "total": total, "percent": round(percent, 2)}


def _compute_pairwise_coverage(pairs: list[Tuple[str, str]], seen: set[Tuple[str, str]]) -> dict[str, float | int]:
    """Compute coverage stats for a pairwise category set."""

    total = len(pairs)
    covered = len({pair for pair in pairs if pair in seen})
    percent = (covered / total) * 100 if total else 0.0
    return {"covered": covered, "total": total, "percent": round(percent, 2)}


def main() -> int:
    """Generate combinatorial cases and coverage metrics."""

    args = parse_args()

    mobile_classes = ["valid", "missing_plus", "too_short", "too_long", "non_digit"]
    message_classes = [
        "valid",
        "invalid_prefix",
        "unknown_sku",
        "qty_zero",
        "qty_too_large",
        "too_many_items",
    ]
    auth_classes = ["correct", "incorrect"]

    cases: list[dict[str, object]] = []
    mobile_seen: set[str] = set()
    message_seen: set[str] = set()
    auth_seen: set[str] = set()
    pair_mm_seen: set[Tuple[str, str]] = set()
    pair_ma_seen: set[Tuple[str, str]] = set()
    pair_aa_seen: set[Tuple[str, str]] = set()

    case_index = 1
    for mobile_class in mobile_classes:
        for message_class in message_classes:
            for auth_class in auth_classes:
                mobile, _, _ = _build_mobile(mobile_class)
                message, _, _ = _build_message(message_class)
                expected_ok, expected_error_code = _expected_result(
                    mobile_class, message_class
                )
                auth_value = "123456" if auth_class == "correct" else "000000"
                if not expected_ok:
                    auth_value = ""
                case = {
                    "case_id": f"C{case_index:03d}",
                    "mobile_class": mobile_class,
                    "message_class": message_class,
                    "auth_class": auth_class,
                    "mobile": mobile,
                    "message": message,
                    "auth": auth_value,
                    "expected_ok": expected_ok,
                    "expected_error_code": expected_error_code,
                }
                cases.append(case)
                case_index += 1
                mobile_seen.add(mobile_class)
                message_seen.add(message_class)
                auth_seen.add(auth_class)
                pair_mm_seen.add((mobile_class, message_class))
                pair_ma_seen.add((mobile_class, auth_class))
                pair_aa_seen.add((message_class, auth_class))

    cases_payload = {
        "generated_at": _utc_now(),
        "categories": {
            "mobile_class": mobile_classes,
            "message_class": message_classes,
            "auth_class": auth_classes,
        },
        "cases": cases,
    }

    pair_mm = [(m, msg) for m in mobile_classes for msg in message_classes]
    pair_ma = [(m, auth) for m in mobile_classes for auth in auth_classes]
    pair_aa = [(msg, auth) for msg in message_classes for auth in auth_classes]

    coverage_payload = {
        "generated_at": _utc_now(),
        "num_cases": len(cases),
        "category_coverage": {
            "mobile_class": _compute_category_coverage(mobile_classes, mobile_seen),
            "message_class": _compute_category_coverage(message_classes, message_seen),
            "auth_class": _compute_category_coverage(auth_classes, auth_seen),
        },
        "pairwise_coverage": {
            "mobile_class:message_class": _compute_pairwise_coverage(pair_mm, pair_mm_seen),
            "mobile_class:auth_class": _compute_pairwise_coverage(pair_ma, pair_ma_seen),
            "message_class:auth_class": _compute_pairwise_coverage(pair_aa, pair_aa_seen),
        },
    }

    args.cases_out.parent.mkdir(parents=True, exist_ok=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.cases_out.write_text(json.dumps(cases_payload, sort_keys=True, indent=2), encoding="utf-8")
    args.out.write_text(json.dumps(coverage_payload, sort_keys=True, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
