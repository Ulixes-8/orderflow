# LO3.1 Implemented vs planned testing

This section answers: "How well do implemented tests compare with the planned testing?"

Plan basis:
- docs/lo2/test_inventory.csv is the authoritative list of planned tests.

Evidence:
- artifacts/plan_status.json is the mechanically generated summary.
- artifacts/junit.xml provides execution status evidence.

## Summary (fill after running evidence)

- Planned tests (from LO2 inventory): <N_PLANNED>
- Implemented tests discovered: <N_IMPLEMENTED>
- Passing: <N_PASS>
- Failing: <N_FAIL>
- Skipped: <N_SKIP>
- Deferred: <N_DEFERRED>

## Table: planned vs implemented

Fill this table from artifacts/plan_status.json (or auto-generated report).

Columns:
- Planned Test ID: from docs/lo2/test_inventory.csv
- Level: unit / integration / system / performance / review
- Planned technique: EP/BVA, CLI contract, invariants, etc.
- Linked requirements: LO1 requirement IDs
- Implemented? Y/N
- Location: tests/<...>.py::test_name
- Status: PASS / FAIL / SKIP / XFAIL / DEFERRED
- Notes: defect reference, rationale, or follow-up action

| Planned Test ID | Level | Technique | Linked reqs | Implemented | Location | Status | Notes |
|---|---|---|---|---|---|---|---|
| T-... | ... | ... | R-... | Y/N | ... | ... | ... |

## Notes on deviations from plan

For any deviation from the LO2 plan, record:
- What changed and why (risk discovery, constraints, reprioritisation)
- Whether the deviation weakens adequacy and how it will be mitigated
- Whether the change will be reflected back into LO2 docs (if appropriate)

