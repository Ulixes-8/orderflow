#!/usr/bin/env bash
set -euo pipefail

# LO3 evidence pipeline runner.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACTS_DIR="$ROOT_DIR/docs/lo3/artifacts"
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

mkdir -p "$ARTIFACTS_DIR"

rm -f "$ARTIFACTS_DIR/junit.xml"
rm -f "$ARTIFACTS_DIR/coverage.xml"
rm -f "$ARTIFACTS_DIR/plan_status.json"
rm -f "$ARTIFACTS_DIR/metrics.json"
rm -f "$ARTIFACTS_DIR/model_coverage.json"
rm -f "$ARTIFACTS_DIR/combinatorial_coverage.json"
rm -f "$ARTIFACTS_DIR/combinatorial_cases.json"
rm -f "$ARTIFACTS_DIR/error_codes_exercised.json"
rm -f "$ARTIFACTS_DIR/performance_smoke.json"
rm -rf "$ARTIFACTS_DIR/coverage_html"

pytest -q \
  --junitxml="$ARTIFACTS_DIR/junit.xml" \
  --cov=orderflow \
  --cov-branch \
  --cov-report=term-missing \
  --cov-report=html:"$ARTIFACTS_DIR/coverage_html" \
  --cov-report=xml:"$ARTIFACTS_DIR/coverage.xml"

python "$ROOT_DIR/scripts/lo3_extract_plan_status.py" \
  --inventory "$ROOT_DIR/docs/lo2/test_inventory.csv" \
  --junit-xml "$ARTIFACTS_DIR/junit.xml" \
  --out "$ARTIFACTS_DIR/plan_status.json"

python "$ROOT_DIR/scripts/lo3_compute_metrics.py" \
  --requirements "$ROOT_DIR/docs/lo1/requirements.json" \
  --traceability "$ROOT_DIR/docs/lo1/traceability.csv" \
  --inventory "$ROOT_DIR/docs/lo2/test_inventory.csv" \
  --coverage-xml "$ARTIFACTS_DIR/coverage.xml" \
  --junit-xml "$ARTIFACTS_DIR/junit.xml" \
  --error-codes "$ARTIFACTS_DIR/error_codes_exercised.json" \
  --performance "$ARTIFACTS_DIR/performance_smoke.json" \
  --out "$ARTIFACTS_DIR/metrics.json"

python "$ROOT_DIR/scripts/lo3_model_coverage.py" \
  --out "$ARTIFACTS_DIR/model_coverage.json"

python "$ROOT_DIR/scripts/lo3_combinatorial_generate.py" \
  --out "$ARTIFACTS_DIR/combinatorial_coverage.json" \
  --cases-out "$ARTIFACTS_DIR/combinatorial_cases.json"
