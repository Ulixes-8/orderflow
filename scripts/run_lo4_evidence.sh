#!/usr/bin/env bash
set -euo pipefail

LO4_DIR="docs/lo4"
ARTIFACTS_DIR="${LO4_DIR}/artifacts"
LOG_PATH="${LO4_DIR}/results_log.md"
SUMMARY_PATH="${LO4_DIR}/results_summary.md"

mkdir -p "${ARTIFACTS_DIR}"
mkdir -p "${LO4_DIR}"

: > "${LOG_PATH}"

timestamp() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

log() {
  printf "[%s] %s\n" "$(timestamp)" "$*" | tee -a "${LOG_PATH}"
}

run_cmd() {
  log "CMD: $*"
  "$@" 2>&1 | tee -a "${LOG_PATH}"
}

ensure_lo3_clean() {
  if git diff --name-only -- docs/lo3 | grep -q .; then
    log "ERROR: docs/lo3 has uncommitted changes."
    exit 1
  fi
}

ensure_lo3_clean

export ORDERFLOW_ARTIFACTS_DIR="${ARTIFACTS_DIR}"
export ORDERFLOW_FORBID_LO3_WRITES=1

GIT_COMMIT="$(git rev-parse HEAD)"
LO3_CHECK="git diff --name-only -- docs/lo3 returned empty before and after LO4 run."

log "LO4 evidence run started at $(timestamp)"
log "Git commit: ${GIT_COMMIT}"

run_cmd python scripts/lo4_environment.py --output "${ARTIFACTS_DIR}/environment.json"
ensure_lo3_clean

run_cmd python scripts/lo4_extract_lo3_metrics.py \
  --metrics docs/lo3/artifacts/metrics.json \
  --error-codes docs/lo3/artifacts/error_codes_exercised.json \
  --coverage-output "${ARTIFACTS_DIR}/coverage_from_lo3.json" \
  --failure-output "${ARTIFACTS_DIR}/failure_modes_from_lo3.json"
ensure_lo3_clean

run_cmd python scripts/lo4_targets.py \
  --requirements docs/lo1/requirements.json \
  --output "${ARTIFACTS_DIR}/targets.json"
ensure_lo3_clean

run_cmd python scripts/lo4_benchmark.py \
  --samples-output "${ARTIFACTS_DIR}/performance_samples.json" \
  --stats-output "${ARTIFACTS_DIR}/performance_stats.json"
ensure_lo3_clean

run_cmd python scripts/lo4_compare.py \
  --targets "${ARTIFACTS_DIR}/targets.json" \
  --coverage "${ARTIFACTS_DIR}/coverage_from_lo3.json" \
  --failure-modes "${ARTIFACTS_DIR}/failure_modes_from_lo3.json" \
  --performance "${ARTIFACTS_DIR}/performance_stats.json" \
  --output "${ARTIFACTS_DIR}/comparison.json"
ensure_lo3_clean

run_cmd python scripts/lo4_generate_summary.py \
  --environment "${ARTIFACTS_DIR}/environment.json" \
  --targets "${ARTIFACTS_DIR}/targets.json" \
  --coverage "${ARTIFACTS_DIR}/coverage_from_lo3.json" \
  --failure-modes "${ARTIFACTS_DIR}/failure_modes_from_lo3.json" \
  --performance "${ARTIFACTS_DIR}/performance_stats.json" \
  --comparison "${ARTIFACTS_DIR}/comparison.json" \
  --log "${LOG_PATH}" \
  --summary "${SUMMARY_PATH}" \
  --git-commit "${GIT_COMMIT}" \
  --lo3-check "${LO3_CHECK}"
ensure_lo3_clean

run_cmd python scripts/validate_lo4.py \
  --summary "${SUMMARY_PATH}" \
  --log "${LOG_PATH}" \
  --artifacts "${ARTIFACTS_DIR}"

log "LO4 evidence run completed at $(timestamp)"
