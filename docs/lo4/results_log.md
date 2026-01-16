[2026-01-16T12:30:44Z] LO4 evidence run started at 2026-01-16T12:30:44Z
[2026-01-16T12:30:44Z] Git commit: b85cff0084b716072e42a2ca2a2583522d00dce3
[2026-01-16T12:30:44Z] CMD: python scripts/lo4_environment.py --output docs/lo4/artifacts/environment.json
[2026-01-16T12:30:44Z] CMD: python scripts/lo4_extract_lo3_metrics.py --metrics docs/lo3/artifacts/metrics.json --error-codes docs/lo3/artifacts/error_codes_exercised.json --coverage-output docs/lo4/artifacts/coverage_from_lo3.json --failure-output docs/lo4/artifacts/failure_modes_from_lo3.json
[2026-01-16T12:30:44Z] CMD: python scripts/lo4_targets.py --requirements docs/lo1/requirements.json --output docs/lo4/artifacts/targets.json
[2026-01-16T12:30:44Z] CMD: python scripts/lo4_benchmark.py --samples-output docs/lo4/artifacts/performance_samples.json --stats-output docs/lo4/artifacts/performance_stats.json
[2026-01-16T12:30:57Z] CMD: python scripts/lo4_compare.py --targets docs/lo4/artifacts/targets.json --coverage docs/lo4/artifacts/coverage_from_lo3.json --failure-modes docs/lo4/artifacts/failure_modes_from_lo3.json --performance docs/lo4/artifacts/performance_stats.json --output docs/lo4/artifacts/comparison.json
[2026-01-16T12:30:57Z] CMD: python scripts/lo4_generate_summary.py --environment docs/lo4/artifacts/environment.json --targets docs/lo4/artifacts/targets.json --coverage docs/lo4/artifacts/coverage_from_lo3.json --failure-modes docs/lo4/artifacts/failure_modes_from_lo3.json --performance docs/lo4/artifacts/performance_stats.json --comparison docs/lo4/artifacts/comparison.json --log docs/lo4/results_log.md --summary docs/lo4/results_summary.md --git-commit b85cff0084b716072e42a2ca2a2583522d00dce3 --lo3-check git diff --name-only -- docs/lo3 returned empty before and after LO4 run.
[2026-01-16T12:30:57Z] CMD: python scripts/validate_lo4.py --summary docs/lo4/results_summary.md --log docs/lo4/results_log.md --artifacts docs/lo4/artifacts
LO4 validation OK.
[2026-01-16T12:30:57Z] LO4 evidence run completed at 2026-01-16T12:30:57Z
