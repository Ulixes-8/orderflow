# LO4 Results Summary

## Reproducibility and Integrity Checks
- Version anchor: b85cff0084b716072e42a2ca2a2583522d00dce3
- Environment:
- OS: Linux 6.6.87.2-microsoft-standard-WSL2 (#1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025)
- Python: 3.12.3 (main, Jan  8 2026, 11:30:50) [GCC 13.3.0]
- CPU: AMD Ryzen 9 9950X3D 16-Core Processor
- Cores: 32
- RAM bytes: 32386437120
- Source: docs/lo4/artifacts/environment.json
- Workload definition:
  - place: mobile=+447700900123, message=ORDER COFFEE=1
  - batch: message=ORDER COFFEE=1, lines=20
- Sample sizes and CI:
  - place samples=60, batch samples=60
  - warmup=5, resamples=2000
  - ci_method=bootstrap_percentile
- Commands: see docs/lo4/results_log.md
- docs/lo3 integrity check: git diff --name-only -- docs/lo3 empty before and after run

## LO4.1 Gaps and Omissions
| Gap/Omission | Evidence file(s) | Risk | Mitigation idea |
| --- | --- | --- | --- |
| Missing failure modes (codes not exercised) | docs/lo4/artifacts/failure_modes_from_lo3.json (missing: DATABASE_ERROR, INTERNAL_ERROR, ORDER_ALREADY_FULFILLED) | Unhandled error-code paths could regress or map incorrectly, reducing robustness confidence. | Add deterministic tests to exercise missing codes: DATABASE_ERROR, INTERNAL_ERROR, ORDER_ALREADY_FULFILLED. |
| Performance targets not met with statistical confidence | docs/lo4/artifacts/performance_stats.json (place mean CI [55.927, 56.558] > target 50.0 ms; batch stretch mean CI [139.231, 141.165] > target 80.0 ms; batch stretch p95 CI [144.3, 147.264] > target 140.0 ms; batch throughput stretch mean CI [141.782, 143.732] < target 200.0 lines/sec) | Statistically robust failures against defined targets reduce confidence that measurable performance attributes are satisfied under this workload/environment; risk of user-visible latency and limited headroom under higher load. | Separate cold vs warm performance; profile and reduce overhead; tune DB/transaction strategy; expand operational envelope benchmarks (e.g., batch lines 5/20/50) to validate improvements and generalisation. |
| Context-dependent performance / limited operational envelope | docs/lo4/artifacts/performance_stats.json | Only one workload point per operation was measured, limiting generalizability. | Add envelope benchmarks (batch lines 5/20/50, place payload variants). |
| CLI coverage attribution limitation (subprocess) | docs/lo3/artifacts/metrics.json | Subprocess-based CLI runs produce low coverage attribution, masking CLI regressions. | Add in-process CLI parsing tests or subprocess coverage capture. |
| Weak exploration of exception/fault paths | docs/lo4/artifacts/failure_modes_from_lo3.json | DB fault mapping and defensive paths remain partially untested, leaving residual risk. | Add deterministic fault-injection seams for DB/logic faults. |
| No mutation/fault-based sensitivity estimate | docs/lo4/results_summary.md | Without mutation, confidence in test sensitivity is limited; faults could survive. | Consider mutation testing in LO5 to quantify sensitivity. |
| Statistical assumptions | docs/lo4/artifacts/performance_stats.json | Assumptions such as independent samples and warmup discard may not hold, affecting CI validity (Independent samples with identical workload per run., Warmup runs discarded.). | Re-run benchmarks with randomized ordering and validate assumptions in LO5. |

## LO4.2 Targets and Motivation
| Target | Value | Motivation / Source |
| --- | --- | --- |
| Requirements coverage | >= 100.0% | Source: docs/lo4/artifacts/targets.json |
| Structural coverage orderflow/parser.py | >= 0.90 line / 0.75 branch | Risk-based structural coverage target (LO3 criteria). |
| Structural coverage orderflow/service.py | >= 0.65 line / 0.50 branch | Risk-based structural coverage target (LO3 criteria). |
| Structural coverage orderflow/store/sqlite.py | >= 0.80 line / 0.70 branch | Risk-based structural coverage target (LO3 criteria). |
| Structural coverage orderflow/validation.py | >= 0.90 line / 0.75 branch | Risk-based structural coverage target (LO3 criteria). |
| Failure-mode coverage | All documented error codes exercised | docs/cli_contract.md list. |
| Place performance | mean <= 50.0 ms, p95 <= 120.0 ms | Source: docs/lo4/artifacts/targets.json (from LO1). |
| Batch performance (minimum) | mean <= 150.0 ms, p95 <= 170.0 ms | Minimum acceptable threshold: Minimum acceptable threshold for a 20-line batch on a local developer environment; set above current observed mean/p95 so the target is plausible without immediate optimization. |
| Batch performance (stretch) | mean <= 80.0 ms, p95 <= 140.0 ms | Aspirational threshold: Aspirational headroom goal that requires optimization beyond current baselines. Targets set slightly above LO3 smoke baselines to be realistic while still requiring headroom for batch processing. |
| Batch throughput (minimum) | >= 120.0 lines/sec | Derived from latency samples and known batch line count. |
| Batch throughput (stretch) | >= 200.0 lines/sec | Derived from latency samples and known batch line count. |
| Measurement quality | samples >= 60 (place) / 60 (batch), warmup=5, CI=bootstrap_percentile resamples=2000 | Source: docs/lo4/artifacts/targets.json |

## LO4.3 Achieved vs Target Comparison
| Metric | Achieved (CI) | Target | Pass/Fail | Explanation |
| --- | --- | --- | --- | --- |
| Requirements coverage | 100.0% (n/a) | 100.0% | PASS | Source: docs/lo4/artifacts/coverage_from_lo3.json |
| Coverage orderflow/parser.py | line 0.95, branch 0.91 | line 0.90, branch 0.75 | PASS | Source: docs/lo4/artifacts/coverage_from_lo3.json |
| Coverage orderflow/service.py | line 0.67, branch 0.53 | line 0.65, branch 0.50 | PASS | Source: docs/lo4/artifacts/coverage_from_lo3.json |
| Coverage orderflow/store/sqlite.py | line 0.85, branch 0.75 | line 0.80, branch 0.70 | PASS | Source: docs/lo4/artifacts/coverage_from_lo3.json |
| Coverage orderflow/validation.py | line 0.93, branch 0.75 | line 0.90, branch 0.75 | PASS | Source: docs/lo4/artifacts/coverage_from_lo3.json |
| Failure modes exercised | INVALID_MOBILE, INVALID_QUANTITY, MESSAGE_TOO_LONG, ORDER_NOT_FOUND, PARSE_ERROR, TOO_MANY_ITEMS, UNAUTHORIZED, UNKNOWN_ITEM | DATABASE_ERROR, INTERNAL_ERROR, INVALID_MOBILE, INVALID_QUANTITY, MESSAGE_TOO_LONG, ORDER_ALREADY_FULFILLED, ORDER_NOT_FOUND, PARSE_ERROR, TOO_MANY_ITEMS, UNAUTHORIZED, UNKNOWN_ITEM | FAIL | Missing: DATABASE_ERROR, INTERNAL_ERROR, ORDER_ALREADY_FULFILLED (Source: docs/lo4/artifacts/failure_modes_from_lo3.json) |
| Place mean latency | 56.22 ms (CI [55.927, 56.558]) | <= 50.0 ms | FAIL | Source: docs/lo4/artifacts/performance_stats.json |
| Place p95 latency | 58.502 ms (CI [57.425, 59.511]) | <= 120.0 ms | PASS | Source: docs/lo4/artifacts/performance_stats.json |
| Batch mean latency (minimum) | 140.198 ms (CI [139.231, 141.165]) | <= 150.0 ms | PASS | Source: docs/lo4/artifacts/performance_stats.json |
| Batch p95 latency (minimum) | 146.863 ms (CI [144.3, 147.264]) | <= 170.0 ms | PASS | Source: docs/lo4/artifacts/performance_stats.json |
| Batch mean latency (stretch) | 140.198 ms (CI [139.231, 141.165]) | <= 80.0 ms | FAIL | Source: docs/lo4/artifacts/performance_stats.json |
| Batch p95 latency (stretch) | 146.863 ms (CI [144.3, 147.264]) | <= 140.0 ms | FAIL | Source: docs/lo4/artifacts/performance_stats.json |
| Batch throughput mean (minimum) | 142.758 lines/sec (CI [141.782, 143.732]) | >= 120.0 lines/sec | PASS | Source: docs/lo4/artifacts/performance_stats.json |
| Batch throughput mean (stretch) | 142.758 lines/sec (CI [141.782, 143.732]) | >= 200.0 lines/sec | FAIL | Source: docs/lo4/artifacts/performance_stats.json |

Failure modes exercised: 8/11. Missing: DATABASE_ERROR, INTERNAL_ERROR, ORDER_ALREADY_FULFILLED. Status: FAIL.

Coverage summary: 4 modules compared to targets in docs/lo4/artifacts/coverage_from_lo3.json.

Statistical interpretation:
- Place mean latency: CI [55.927, 56.558] vs target 50.0 -> Fail with high confidence under this workload/environment.
- Batch mean latency (minimum): CI [139.231, 141.165] vs target 150.0 -> Pass with high confidence under this workload/environment.
- Batch mean latency (stretch): CI [139.231, 141.165] vs target 80.0 -> Fail with high confidence under this workload/environment.
- Batch throughput mean (minimum): CI [141.782, 143.732] vs target 120.0 -> Pass with high confidence under this workload/environment.
- Batch throughput mean (stretch): CI [141.782, 143.732] vs target 200.0 -> Fail with high confidence under this workload/environment.

## LO4.4 Actions Needed to Meet/Exceed Targets
| Priority | Action | Gap/Miss addressed | Expected impact | Evidence of completion |
| --- | --- | --- | --- | --- |
| P0 | Add deterministic test for ORDER_ALREADY_FULFILLED (fulfill twice). | Missing failure mode coverage (ORDER_ALREADY_FULFILLED). | Closes error-code gap and improves robustness confidence. | Test ID recorded in LO3/LO4 evidence with passing result. |
| P0 | Add deterministic DB-fault injection seam/test to trigger DATABASE_ERROR mapping. | Missing failure mode coverage (DATABASE_ERROR). | Improves confidence in DB fault handling. | Fault-injection test artifact captures DATABASE_ERROR. |
| P0 | Add controlled invariant-violation seam/test to trigger INTERNAL_ERROR mapping. | Missing failure mode coverage (INTERNAL_ERROR). | Improves defensive-path assurance. | Fault-injection test artifact captures INTERNAL_ERROR. |
| P1 | Performance: split cold vs warm runs and report separately. | Performance CI ambiguity and potential cold-start penalty. | Clarifies warm vs cold impact on latency/throughput. | Separate cold/warm stats included in performance_stats.json. |
| P1 | Performance: add envelope benchmark points (batch lines 5/20/50) without changing CLI contract. | Limited operational envelope coverage. | Improves generalization across workloads. | Additional workload rows in performance_stats.json. |
| P1 | CLI coverage: add in-process parsing/unit tests for CLI argument handling OR subprocess coverage capture. | CLI subprocess coverage attribution limitation. | Improves coverage signal for CLI paths. | Coverage report shows CLI module line/branch rates > 0. |
| P2 | Optional: mutation testing in LO5 (future action). | No mutation/fault-based sensitivity estimate. | Quantifies test sensitivity to seeded faults. | Mutation report included in LO5 artifacts. |

## Overall Confidence Statement
Requirements coverage and core module coverage are strongly supported by LO3-derived
artifacts (docs/lo4/artifacts/coverage_from_lo3.json). Performance evidence is
statistically characterized (docs/lo4/artifacts/performance_stats.json), but
missing failure modes and environment sensitivity reduce confidence in robustness
and performance generality (docs/lo4/artifacts/failure_modes_from_lo3.json).
Assumptions documented in performance_stats.json include: Independent samples with identical workload per run., Warmup runs discarded.
