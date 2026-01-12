# Instrumentation (LO2)

Instrumentation exists to make testing more adequate by increasing visibility into:
- internal state transitions,
- error classification,
- timing/performance behaviour,
- and internal invariants.

## Existing instrumentation (already in repo)
- MetricsCollector: counters + timing series (parse_ms, store_ms, total_ms).
- MetricsStore: persistence of metrics across CLI runs.

## Added instrumentation (this LO2 change)
### 1) Diagnostics sink (off by default)
- Optional JSON Lines diagnostics log (file) that records:
  - command starts/success,
  - key intermediate values (validated mobile, parsed SKUs),
  - error events (code/message/details),
  - invariant failures (if detected).
- This is *never* written to stdout, so it cannot break the CLI contract or determinism.
- Enabled via `--diagnostics PATH` or `ORDERFLOW_DIAGNOSTICS_PATH`.

### 2) Invariant checks
- Service checks internal consistency for constructed orders:
  - total_pence equals sum of line totals,
  - line_total equals qty * unit_price,
  - quantities are positive,
  - placed orders are PENDING.
- Invariant violations are treated as INTERNAL_ERROR (a deliberate oracle).

## Why this instrumentation helps adequacy
- Improves debugging/triage when tests fail (reduces ambiguity).
- Enables tests to assert “no side effects” using diagnostics + repo state.
- Supports auditing: shows what was instrumented and why.
