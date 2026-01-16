# LO5.3 Testing Automation in CI

This document defines which tests would be merge-gating versus nightly, with
exact command snippets for each stage.

## Merge-gating (PR and push)

### Stage 0: Validators

```bash
python scripts/validate_lo1.py
python scripts/validate_lo2.py
python scripts/validate_lo4.py
python scripts/validate_lo5.py --summary docs/lo5/results_summary.md \
  --log docs/lo5/results_log.md --artifacts docs/lo5/artifacts/<run_id>
```

### Stage 1: Unit and integration tests (fast)

```bash
pytest -q --disable-warnings --maxfail=1 --junitxml docs/lo5/artifacts/<run_id>/junit.xml
```

These tests are merge-gating because they are expected to be fast and provide
quick feedback on functional regressions.

### Stage 2: System/contract tests (if stable)

If contract tests are stable and fast, include them as merge-gating. Otherwise,
move them to nightly. Example (placeholder):

```bash
pytest -q tests/contract --disable-warnings --maxfail=1 \
  --junitxml docs/lo5/artifacts/<run_id>/junit_contract.xml
```

## Nightly (non-gating)

### Stage 3: Extended checks and LO4 benchmark runner

```bash
python scripts/run_lo4_benchmarks.py
```

Nightly is used for heavier or flakier checks, such as LO4 performance
benchmarks, to avoid slowing down PR iterations. These runs are informative
and non-gating, but failures should be triaged promptly.

## Mapping to existing evidence tooling

- `validate_lo1.py`: Ensures LO1 artifacts are complete and consistent.
- `validate_lo2.py`: Ensures LO2 artifacts are complete and consistent.
- `validate_lo4.py`: Ensures LO4 evidence is consistent and traceable.
- `validate_lo5.py`: Ensures LO5 evidence is complete and coherent.
- `pytest`: Runs unit and integration tests with JUnit outputs.
- LO4 runner: Runs nightly performance benchmarks and evidence collection.
