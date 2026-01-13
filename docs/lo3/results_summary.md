# LO3.3 Results of testing — Summary

This section gives a concise overview of test results and points to detailed artifacts.

## A) Test execution summary (fill from artifacts/junit.xml)
- Total tests executed: <N_TOTAL>
- Passing: <N_PASS>
- Failing: <N_FAIL>
- Skipped: <N_SKIP>
- Expected failures (XFAIL): <N_XFAIL>

Breakdown by level:
- Unit: <N_UNIT>
- Integration: <N_INT>
- System: <N_SYS>
- Property-based: <N_PROP>
- Model-based: <N_MODEL>
- Combinatorial: <N_COMBO>

## B) Coverage summary (fill from artifacts/coverage.xml)
Core modules (line %, branch %):
- orderflow/service.py: <LINE>% line, <BRANCH>% branch
- orderflow/parser.py:  <LINE>% line, <BRANCH>% branch
- orderflow/validation.py: <LINE>% line, <BRANCH>% branch
- orderflow/store/sqlite.py: <LINE>% line, <BRANCH>% branch
- orderflow/cli.py: <LINE>% line, <BRANCH>% branch

Reports:
- HTML: docs/lo3/artifacts/coverage_html/index.html
- XML: docs/lo3/artifacts/coverage.xml

## C) Technique coverage (brief)
- Functional EP/BVA + negative testing: Y/N
- Integration boundary + invariants: Y/N
- System CLI contract tests (exit codes + stdout schema): Y/N
- Structural coverage computed: Y/N
- Combinatorial testing (category + bounded pairwise): Y/N
- Model-based testing (FSM state/transition coverage): Y/N
- Property-based testing (Hypothesis): Y/N

## D) Yield (defects and failures)
Defects found (unique, with references):
- D-001: <title> (found by <technique>) -> fix: <commit/ref>
- D-002: ...

Failure yield trend (from results_log.md):
- Early runs: <...>
- Later runs: <...>

## E) Performance (baseline only in LO3)
Baseline performance evidence (smoke):
- Place mean/p95 (sample): <...>
- Batch throughput (sample): <...>

Formal statistical characterization and target evaluation are in LO4.

## Pointers to detailed evidence
- Planned vs implemented: docs/lo3/implemented_vs_planned.md
- Detailed run log: docs/lo3/results_log.md
- Evaluation interpretation: docs/lo3/evaluation_results.md
- Generated artifacts: docs/lo3/artifacts/

