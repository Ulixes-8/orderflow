# LO3.3 Results of testing — Summary

This section gives a concise overview of test results and points to detailed artifacts.

## A) Test execution summary
- Total tests executed: 30
- Passing: 30
- Failing: 0
- Skipped: 0
- Expected failures (XFAIL): 0

Breakdown by level:
- Unit: 6
- Integration: 7
- System: 11
- Review: 2
- Performance: 2
- Property-based: 1
- Model-based: 0 (model coverage is reported via artifacts/model_coverage.json)
- Combinatorial: 1

## B) Coverage summary
Core modules (line %, branch %):
- orderflow/service.py: 67.03% line, 52.94% branch
- orderflow/parser.py:  95.24% line, 90.91% branch
- orderflow/validation.py: 93.18% line, 75.00% branch
- orderflow/store/sqlite.py: 85.00% line, 75.00% branch
- orderflow/cli.py: 0.00% line, 0.00% branch

Reports:
- HTML: docs/lo3/artifacts/coverage_html/index.html
- XML: docs/lo3/artifacts/coverage.xml

## C) Technique coverage (brief)
- Functional EP/BVA + negative testing: Y
- Integration boundary + invariants: Y
- System CLI contract tests (exit codes + stdout schema): Y
- Structural coverage computed: Y
- Combinatorial testing (full cross-product; pairwise adequacy): Y
- Model-based testing (FSM state/transition coverage): Y
- Property-based testing (Hypothesis): Y

## D) Yield (defects and failures)
Defects found (unique, with references):
- None recorded in the LO3 evidence run.

Failure yield trend (from results_log.md):
- Early runs: no failures recorded.
- Later runs: no failures recorded.

## E) Performance (baseline only in LO3)
Baseline performance evidence (smoke):
- Place mean/p95 (sample): 51.605ms / 56.589ms
- Batch mean/p95 (sample): 55.446ms / 57.532ms
- Batch throughput (derived, 2-line batch):
  - Formula: lines/sec = 2 / (ms / 1000) = 2000 / ms
  - Mean/p95 throughput: 36.099 / 37.141 lines/sec

Formal statistical characterization and target evaluation are in LO4.

## Pointers to detailed evidence
- Planned vs implemented: docs/lo3/implemented_vs_planned.md
- Detailed run log: docs/lo3/results_log.md
- Evaluation interpretation: docs/lo3/evaluation_results.md
- Generated artifacts: docs/lo3/artifacts/
