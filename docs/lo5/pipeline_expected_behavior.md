# LO5.4 Expected CI Pipeline Behavior

The table below documents expected pipeline behavior for common issue types.
Each issue lists how it is detected, which stage detects it, and what evidence
artifact captures the failure.

| Issue type | Pipeline stage | Detector (validator/test/review-check) | Failure signal | Evidence artifact |
| --- | --- | --- | --- | --- |
| LO artifact drift (traceability/plan mismatch) | Stage 0 | `validate_lo1.py`, `validate_lo2.py`, `validate_lo4.py`, `validate_lo5.py` | Non-zero exit + validator error output | Validator stderr logs + results summary |
| CLI contract regression (stdout schema/exit codes) | Stage 2 | Contract tests or CLI golden tests | Test failure with schema diff or exit code mismatch | JUnit XML + contract test logs |
| Non-parameterized SQL introduced | Stage 0 | `lo5_review_checks.py` SQL heuristic | P1/P2 finding in review findings JSON | `review_findings.json` |
| Missing failure-mode mapping/regression | Stage 0/1 | `lo5_review_checks.py` + unit tests | P2 opportunity finding or test failure | `review_findings.json` + JUnit XML |
| Diagnostics contaminates stdout or breaks determinism | Stage 0/2 | Review checks + contract tests | Finding in review checks or contract test failure | `review_findings.json` + contract logs |
| Unit regression in parser/validation | Stage 1 | `pytest` unit suite | Unit test failure | JUnit XML |
| Integration regression (DB invariant / partial write handling) | Stage 1 | `pytest` integration tests | Integration test failure | JUnit XML + captured logs |
| Performance regression (nightly LO4 benchmark exceeding minimum targets) | Nightly | LO4 benchmark runner | Benchmark report below minimum thresholds | LO4 benchmark artifacts |
