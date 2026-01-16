#!/usr/bin/env bash
set -euo pipefail

LOG_PATH="docs/lo5/results_log.md"
RUN_ID="$(date -u +"%Y%m%dT%H%M%SZ")"
RUN_DIR="docs/lo5/artifacts/run_${RUN_ID}"
GIT_COMMIT="$(git rev-parse HEAD)"

mkdir -p "$RUN_DIR"
touch "$LOG_PATH"

log_line() {
  printf "%s\n" "$1" >> "$LOG_PATH"
}

log_block() {
  printf "%s\n" "$1" >> "$LOG_PATH"
}

run_cmd() {
  log_line "COMMAND: $*"
  "$@" 2>&1 | tee -a "$LOG_PATH"
}

log_block "## LO5 Evidence Run ${RUN_ID}"
log_line "start_timestamp_utc: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
log_line "git commit: ${GIT_COMMIT}"

log_line "COMMAND: git diff --name-only -- docs/lo3"
LO3_DIFF_PRE="$(git diff --name-only -- docs/lo3)"
if [[ -n "$LO3_DIFF_PRE" ]]; then
  log_line "LO3 diff check: non-empty"
  log_block "$LO3_DIFF_PRE"
  exit 1
else
  log_line "LO3 diff check: empty"
fi

export ORDERFLOW_FORBID_LO3_WRITES=1
export ORDERFLOW_ARTIFACTS_DIR="$RUN_DIR"

run_cmd python scripts/lo5_environment.py --output "${RUN_DIR}/environment.json"
run_cmd python scripts/lo5_review_checks.py --output "${RUN_DIR}/review_findings.json"
run_cmd python scripts/validate_lo1.py
run_cmd python scripts/validate_lo2.py
run_cmd python scripts/validate_lo4.py
run_cmd pytest -q --disable-warnings --maxfail=1 \
  --junitxml "${RUN_DIR}/junit.xml"
run_cmd python scripts/lo5_generate_summary.py \
  --environment "${RUN_DIR}/environment.json" \
  --review-findings "${RUN_DIR}/review_findings.json" \
  --log "${LOG_PATH}" \
  --summary "docs/lo5/results_summary.md" \
  --git-commit "${GIT_COMMIT}" \
  --run-dir "${RUN_DIR}"
run_cmd python scripts/validate_lo5.py \
  --summary "docs/lo5/results_summary.md" \
  --log "${LOG_PATH}" \
  --artifacts "${RUN_DIR}"

log_line "COMMAND: git diff --name-only -- docs/lo3"
LO3_DIFF_POST="$(git diff --name-only -- docs/lo3)"
if [[ -n "$LO3_DIFF_POST" ]]; then
  log_line "LO3 diff check: non-empty"
  log_block "$LO3_DIFF_POST"
  exit 1
else
  log_line "LO3 diff check: empty"
fi

log_line "end_timestamp_utc: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
