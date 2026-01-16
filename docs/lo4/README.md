# LO4 Evidence Pack — Targets, Comparison, Improvements

This folder contains the LO4 evidence pipeline outputs. The pipeline is
non-destructive to LO3 artifacts and only reads from `docs/lo3/`.

## Run LO4 evidence

```bash
bash scripts/run_lo4_evidence.sh
```

The runner produces:

- `docs/lo4/results_summary.md`
- `docs/lo4/results_log.md`
- `docs/lo4/artifacts/` (JSON evidence files)

## Safety notes

- The LO4 runner fails fast if any writes to `docs/lo3/` are detected.
- The pytest session hook is redirected via `ORDERFLOW_ARTIFACTS_DIR`.
- `ORDERFLOW_FORBID_LO3_WRITES=1` is enforced by the LO4 runner.
