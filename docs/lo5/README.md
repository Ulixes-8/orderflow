# LO5 Evidence Pack

This folder contains the LO5 review documentation, evidence artifacts, and
automation scripts needed to generate a reproducible evidence pack. All LO5
artifacts are intentionally isolated from LO3 outputs to avoid any accidental
cross-contamination of evidence. The evidence runner enforces this isolation by
exporting `ORDERFLOW_FORBID_LO3_WRITES=1` and writing into a unique
`docs/lo5/artifacts/run_run_20260116T141547Z/` directory.

## Contents

- `review_criteria.md`: Review checklist and rationale (LO5.1).
- `review_scope.md`: Scope and rationale for what was reviewed (LO5.1).
- `review_report.md`: Findings table and review summary (LO5.1).
- `ci_pipeline_design.md`: CI design proposal (design only; not implemented)
  (LO5.2).
- `testing_in_ci.md`: Proposed CI testing stages and commands (LO5.3).
- `pipeline_expected_behavior.md`: Expected CI failure detection examples
  (LO5.4).
- `results_summary.md`: Generated summary from the LO5 runner.
- `results_log.md`: Generated log of commands and integrity checks.
- `artifacts/`: Machine-readable outputs from the LO5 runner.

## Regenerating Evidence

Run the LO5 evidence runner:

```bash
./scripts/run_lo5_evidence.sh
```

The runner will create a unique run directory under `docs/lo5/artifacts/`,
record all commands in `results_log.md`, and generate `results_summary.md`.
