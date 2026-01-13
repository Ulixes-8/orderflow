# LO3.1 Range of testing techniques used

This section answers: "Did we apply a wide variety of testing techniques?"

The course expects more than "many unit tests". This evidence pack uses:
- Requirements-based functional testing (EP/BVA + negative testing)
- Integration testing (DB boundary + invariants)
- System testing (CLI contract + golden outputs)
- Structural evaluation (line/branch coverage)
- Combinatorial testing (category-partition + bounded pairwise)
- Model-based testing (FSM state/transition coverage)
- Property-based testing (Hypothesis robustness checks)

## Technique 1: Functional requirements-based testing
- Unit: parser and validation partitions (EP/BVA + negative tests)
- Evidence: pytest tests under tests/unit/*
- Adequacy signal: requirements coverage + error-code yield

## Technique 2: Integration testing at boundaries
- SQLite repository semantics, state invariants, injection-style strings
- Evidence: tests/integration/*
- Adequacy signal: invariant preservation; correct error mapping; no side effects

## Technique 3: System testing (CLI contract)
- CLI output schema, exit codes, determinism, batch streaming behavior
- Evidence: tests/system/* and docs/cli_contract.md
- Adequacy signal: contract compliance + golden output regression stability

## Technique 4: Structural evaluation (coverage)
- Line/branch coverage from pytest-cov artifacts
- Evidence: artifacts/coverage.xml and artifacts/coverage_html/
- Adequacy signal: coverage thresholds, plus justification of exclusions

## Technique 5: Combinatorial testing
- Category-partition + bounded pairwise generation for input interactions
- Evidence: artifacts/combinatorial_coverage.json plus generated cases
- Adequacy signal: partition coverage and pairwise coverage %

## Technique 6: Model-based testing
- FSM model of order lifecycle; state + transition coverage
- Evidence: artifacts/model_coverage.json and scripts/lo3_model_spec.md
- Adequacy signal: transition coverage for key lifecycle behaviors

## Technique 7: Property-based testing (Hypothesis)
- Robustness and edge-case discovery for parser and validation
- Evidence: tests/property/*
- Adequacy signal: counterexamples found (yield) and regression lock-in

