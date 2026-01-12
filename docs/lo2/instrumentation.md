# Instrumentation (LO2)

Instrumentation exists to make testing more adequate by increasing visibility into:
- internal state transitions,
- error classification,
- timing/performance behaviour,
- and internal invariants.

A key constraint for auditability and system-level testing is that **stdout remains reserved
for the CLI JSON contract** (deterministic, regression-testable). Therefore, diagnostics are
**never written to stdout** and are **off by default** unless explicitly enabled.

## Existing instrumentation (already in repo)
- **MetricsCollector**: counters + timing series (e.g., `parse_ms`, `store_ms`, `total_ms`)
  to support performance investigation and trend analysis without adding test-only
  behaviour.
- **MetricsStore**: persistence of metrics across CLI runs (supports operational visibility
  requirements and performance evidence).

## Added instrumentation (this LO2 change)

### 1) Diagnostics sink (off by default; file-only)
We added an optional diagnostics subsystem that can write **JSON Lines** events to a file.
This is explicitly separated from stdout to preserve the CLI contract and determinism.

**How to enable**
- CLI flag: `--diagnostics PATH`
- Environment variable: `ORDERFLOW_DIAGNOSTICS_PATH`

**What is recorded (current implementation)**
Diagnostics events are recorded primarily for the `place` workflow plus a cross-cutting
error event:
- `place.start`: command start with basic request metadata (e.g., mobile, message length)
- `place.mobile_ok`: canonicalised/validated mobile
- `place.parsed`: parsed SKU set/count (post-grammar/limits validation)
- `place.stored`: order persisted (e.g., order_id, totals)
- `error`: cross-cutting error event with `code`, `message`, and optional `details`
  (recorded whenever a request returns an error response)

**Important scope note (audit precision)**
At present, the “start/success-style” diagnostics are implemented for `place` and errors are
recorded generically via the shared error handler. Equivalent start/success events for other
commands (e.g., `list`, `show`, `fulfill`, `batch`) are not required for correctness but could be
added if future diagnosis or tests justify them.

### 2) Invariant checks (deliberate oracle)
We added service-level invariant checks for constructed orders to provide a strong internal
consistency oracle:
- `total_pence` equals the sum of line totals,
- `line_total` equals `qty * unit_price`,
- quantities are positive,
- newly placed orders are `PENDING`.

Invariant violations are treated as `INTERNAL_ERROR`. This is deliberate: it converts silent
inconsistency into an explicit, testable failure mode.

## Why this instrumentation helps adequacy
- Improves debugging/triage when tests fail (reduces ambiguity, faster fault localisation).
- Enables tests to assert “no side effects” using diagnostics + repository state (especially
  for integration/safety requirements where return codes alone are insufficient).
- Supports audit realism: we document both what we instrumented and what we did not,
  and we keep instrumentation optional/off-by-default to avoid undermining performance
  targets when diagnostics are disabled.
