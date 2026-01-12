# Evaluation of instrumentation adequacy (LO2)

## What it does well
- Adds visibility without contaminating stdout contract.
- Keeps overhead optional (off by default) so it does not undermine performance targets.
- Invariant checks provide a strong oracle for internal consistency.

## Limitations
- Diagnostics are per-process and do not provide cross-process correlation IDs.
- Invariants cannot prove business correctness; they only detect internal inconsistency.
- Diagnostics do not currently record DB transaction boundaries explicitly.

## Potential improvements (documented for audit realism)
- Add correlation IDs per command execution (for larger systems).
- Add optional transaction boundary events in repository layer.
- Add sampling controls for performance logging to reduce overhead when enabled.
