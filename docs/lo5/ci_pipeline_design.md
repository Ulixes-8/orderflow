# LO5.2 CI Pipeline Design (Design Only; Not Implemented)

This document is **design only; not implemented**. It describes a proposed CI
pipeline structure for reproducible evidence collection and contract integrity,
without adding any actual workflow automation or third-party tooling.

## Triggers

- **Pull request / push:** Run the fast validation and test stages on every PR
  and on merge to the default branch.
- **Nightly:** Run extended checks and LO4 benchmarks to catch regressions that
  are too slow or flaky for merge gating.

## Stages and rationale

### Stage 0: Policy and validators

Run LO validators to ensure evidence and documentation are consistent and
artifacts are complete.

- `python scripts/validate_lo1.py`
- `python scripts/validate_lo2.py`
- `python scripts/validate_lo4.py`
- `python scripts/validate_lo5.py`

### Stage 1: Unit and integration tests (fast)

Run fast unit and integration tests to catch functional regressions early. This
stage is intended to be merge gating.

### Stage 2: System and contract tests

Run contract tests or system-level workflows that validate CLI behavior and
stdout JSON contracts. If these are unstable, run them on merge or nightly.

### Stage 3: Reporting and artifacts

Collect JUnit XML, validator outputs, and summary artifacts for auditability.
This stage focuses on traceability rather than gating.

### Nightly: Extended checks and LO4 benchmarks

Run performance benchmarks and extended checks in a non-destructive, isolated
environment. LO4 benchmarking should be nightly to avoid slowing PR iteration.

## Artifacts and retention

Expected artifacts include:

- Validator logs and summaries (LO1/LO2/LO4/LO5).
- JUnit XML from pytest.
- LO4 benchmark outputs (nightly only).
- Environment snapshots and review findings.

Retention should preserve at least the latest 30 nightly runs and at least 10
PR runs for traceability, with older artifacts pruned for storage control.
