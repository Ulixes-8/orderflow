# Plan evolution (TDD-oriented) — LO2

This log exists to demonstrate that the test plan evolves as functionality and
requirements drive development (TDD principle advocated by the course).

## Iteration 0 — Baseline (from LO1)
- Established requirements catalogue and requirement→technique mapping.
- Established traceability IDs (planned tests).

## Iteration 1 — Parser/validation first (unit safety net)
Trigger: robustness requirements for grammar/limits and invalid inputs.
- Added unit EP/BVA partitions for:
  - mobile validation, message length
  - ORDER grammar, empty items, max items, qty boundaries
- Rationale: fastest feedback, highest diagnostic value.

## Iteration 2 — Persistence boundary + state invariants
Trigger: safety/security/integration requirements.
- Added integration tests for:
  - unauthorized fulfill causes no persisted transition
  - DB failure handling avoids partial writes
  - injection-style malicious strings at DB boundary

## Iteration 3 — End-to-end CLI contracts + regression stability
Trigger: system-level requirements and determinism.
- Added CLI system tests for:
  - place/list/show/fulfill exit codes and JSON schema
  - golden-output determinism checks

## Iteration 4 — Performance sampling (deferred)
Trigger: measurable quality attributes.
- Planned repeated sampling and statistical summaries (formalised in LO4),
  explicitly acknowledging environmental noise.
