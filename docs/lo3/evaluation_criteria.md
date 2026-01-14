# LO3.2 Evaluation criteria for adequacy of testing

This section answers:
- What metrics do we use to judge adequacy?
- Why are these metrics appropriate for each technique?
- What assumptions can mislead us (optimistic/pessimistic/simplified), and what mitigations do we apply?

All metrics are "evidence signals", not proofs.

## A) Requirements coverage (traceability coverage)
Metric:
- % of LO1 requirements with >= 1 passing test mapped in LO2 inventory

Data sources:
- docs/lo1/requirements.json
- docs/lo1/traceability.csv
- docs/lo2/test_inventory.csv
- artifacts/junit.xml

Assumptions / pitfalls:
- Assumes the mapping from requirements -> tests is correct.
- Passing tests can have weak oracles (assertions too weak).
- A single test might only partially cover a requirement.

Mitigations:
- Keep mappings explicit (implemented_vs_planned.md).
- Prefer tests with strong oracles (invariants + explicit error codes).
- For highlight requirements, require at least one system or integration test.

## B) Structural coverage (line and branch coverage)
Metrics:
- Line coverage % (core modules)
- Branch coverage % (core modules)

Data sources:
- artifacts/coverage.xml
- artifacts/coverage_html/

Assumptions / pitfalls:
- High coverage does not imply fault detection (weak assertions).
- Coverage can miss data-flow and semantic errors.
- Some defensive paths may be unreachable under normal execution.

Mitigations:
- Combine coverage with yield: ensure failures/defects are actually detected.
- Add targeted negative tests for uncovered error paths where meaningful.
- Justify exclusions explicitly (unreachable/defensive) in evaluation_results.md.

Targets (risk-based, per module):
- Parser + validation: >= 90% line, >= 75% branch (highest risk for input acceptance)
- SQLite repository: >= 80% line, >= 70% branch (data integrity + error mapping)
- Service: >= 65% line, >= 50% branch (thin orchestration, error wrapping)
- CLI subprocess execution is evaluated via contract tests; structural
  coverage for the CLI is reported but not used as a primary adequacy
  target because subprocess coverage is not aggregated in LO3.
These thresholds are risk-based: modules that validate or parse user
input are held to a higher bar than orchestration layers.

## C) Combinatorial coverage
Metrics:
- Category coverage: each category value exercised at least once
- Pairwise coverage % within a bounded subset of categories, even when
  the full cross-product is enumerated for small, bounded sets

Assumptions / pitfalls:
- Pairwise does not guarantee higher-order interaction coverage.
- Generated combinations may include invalid/irrelevant cases if constraints are weak.

Mitigations:
- Define constraints in scripts/lo3_combinatorial_plan.md.
- Add a small number of targeted 3-way cases for known risky intersections.
- Record which constraints were applied and why.

## D) Model-based coverage (FSM)
Metrics:
- State coverage % (visited states / defined states)
- Transition coverage % (visited transitions / defined transitions)

Assumptions / pitfalls:
- Model incompleteness: the FSM may omit real behaviors or error modes.
- Overfitting: model might encode implementation quirks rather than requirements.

Mitigations:
- Keep the model minimal and requirement-aligned.
- Document omissions explicitly (what the model does not attempt to cover).
- Treat model-based tests as complementary to functional and contract tests.

## E) Yield (effectiveness) metrics
Metrics:
- Defect yield per technique (# unique defects found and fixed)
- Failure yield (# failed tests / # executed tests) over time
- Error-code yield (# distinct error codes exercised) for robustness/validation
- (Optional) Mutation-yield proxy (mutants killed / total) if used

Assumptions / pitfalls:
- Yield depends on development stage (early yield high, later yield low).
- A low yield can mean either "high quality" or "weak tests".

Mitigations:
- Maintain a results_log.md showing when defects were discovered and fixed.
- Use multiple techniques to avoid relying on one weak signal.
- Use strong oracles (invariants, explicit error codes, state checks).

## Performance note (LO3 vs LO4)
LO3 includes baseline performance smoke evidence only (sanity checks).
Formal statistical characterization and target evaluation are handled in LO4.
