# LO3 Evidence Pack — Variety of techniques + coverage + yield

This folder contains the evidence for LO3:

3. Apply a wide variety of testing techniques and compute test coverage and
yield according to a variety of criteria.

This evidence pack is designed to be audit-friendly:
- It is explicit about what was planned (LO2) vs what was implemented (LO3).
- It defines evaluation criteria (coverage and yield) and their limitations.
- It presents results in a readable summary and provides drill-down logs.
- It includes generated artifacts (coverage reports, junit, metrics JSON).

## Inputs (test basis and plan basis)

LO1 basis:
- docs/lo1/requirements.json
- docs/lo1/traceability.csv

LO2 plan basis:
- docs/lo2/test_inventory.csv
- docs/lo2/test_plan.md

System-test contract basis:
- docs/cli_contract.md

## Outputs (this folder)

Core narrative docs:
- implemented_vs_planned.md  (LO3.1)
- techniques.md              (LO3.1)
- evaluation_criteria.md     (LO3.2)
- results_summary.md         (LO3.3)
- results_log.md             (LO3.3)
- evaluation_results.md      (LO3.4)

Generated artifacts (do not hand-edit):
- artifacts/coverage_html/           (HTML coverage report)
- artifacts/coverage.xml             (Coverage XML)
- artifacts/junit.xml                (Test results)
- artifacts/metrics.json             (Computed coverage/yield metrics)
- artifacts/plan_status.json         (Planned vs implemented extraction)
- artifacts/model_coverage.json      (Model-based coverage)
- artifacts/combinatorial_coverage.json (Combinatorial coverage)

## How to regenerate evidence

From repo root, run:
- bash scripts/run_lo3_evidence.sh

If the evidence scripts are not implemented yet, this README defines the
expected artifacts so the LO3 narrative remains consistent as the scripts
are completed.

## Conventions for auditability

1) Include the LO2 test ID in each implemented test name or marker.
   Example: test_T_SYS_ERRCODES_001_invalid_mobile_exit_2

2) When something is not implemented, mark it explicitly:
   - DEFERRED: not done, with reason and a planned next step
   - SKIP: skipped intentionally (e.g., platform constraints), with reason
   - XFAIL: expected failure (known defect), with defect reference

3) Performance evaluation positioning:
   - LO3 includes baseline smoke evidence only.
   - Formal statistical characterization and target evaluation are in LO4.

