"""Diagnostics sinks for OrderFlow instrumentation.

The goal is to increase observability for testing without contaminating the
user-facing CLI contract (stdout JSON). Diagnostics are therefore written to
an optional sink (typically JSON Lines file) and are OFF by default.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Protocol


class DiagnosticsSink(Protocol):
    """Protocol for receiving diagnostic events."""

    def record(self, event: str, payload: Mapping[str, object] | None = None) -> None:
        """Record a diagnostic event."""

    def close(self) -> None:
        """Release any resources held by the sink."""


class NullDiagnosticsSink:
    """A no-op diagnostics sink (default)."""

    def record(self, event: str, payload: Mapping[str, object] | None = None) -> None:
        return

    def close(self) -> None:
        return


@dataclass
class JsonLinesDiagnosticsSink:
    """Write diagnostics events as JSON Lines to a file."""

    path: Path

    def __post_init__(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.path.open("a", encoding="utf-8")

    def record(self, event: str, payload: Mapping[str, object] | None = None) -> None:
        entry: dict[str, object] = {
            "ts_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "event": event,
        }
        if payload:
            entry["payload"] = dict(payload)
        self._fh.write(json.dumps(entry, sort_keys=True))
        self._fh.write("\n")
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()


class InMemoryDiagnosticsSink:
    """Store diagnostics events in memory (useful for unit tests)."""

    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    def record(self, event: str, payload: Mapping[str, object] | None = None) -> None:
        entry: dict[str, object] = {"event": event}
        if payload:
            entry["payload"] = dict(payload)
        self.events.append(entry)

    def close(self) -> None:
        return


def build_diagnostics_sink(path: str | None) -> DiagnosticsSink:
    """Build a diagnostics sink from an optional path."""
    if path is None or not str(path).strip():
        return NullDiagnosticsSink()
    return JsonLinesDiagnosticsSink(Path(path))
