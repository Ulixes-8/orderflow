# LO2 Evidence Pack — Test Planning + Instrumentation

This folder contains the evidence referenced by the portfolio for:

LO2: Design and implement comprehensive test plans with instrumented code.

LO2 expectations (per course guidance):
- a test plan consistent with LO1 requirements + test approaches,
- evidence that the plan evolves (TDD-oriented),
- instrumentation that improves observability for adequate testing,
- evaluation of both plan quality and instrumentation adequacy/limitations.

## Contents
- test_plan.md
  ISO/IEC 29119-inspired test plan (scope, items, approach, criteria, risks, deliverables).
- test_inventory.csv
  Test IDs (aligned with LO1 traceability) with level/technique/rationale.
- plan_evolution.md
  TDD-style evolution log: how requirements/features drove additions to the test set.
- plan_review.md
  Strengths/weaknesses, omissions, and vulnerability analysis of the plan.
- instrumentation.md
  What instrumentation exists (metrics + diagnostics + invariants), how to enable, and how it supports testing.
- instrumentation_review.md
  Adequacy assessment + improvements (what it can’t prove / what it misses).

## LO1 links (must remain consistent)
- Canonical requirements: docs/lo1/requirements.json
- Requirement→technique mapping: docs/lo1/test-approach.md
- Traceability (req → planned test IDs): docs/lo1/traceability.csv
