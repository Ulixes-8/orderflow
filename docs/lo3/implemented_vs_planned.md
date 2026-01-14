# LO3.1 Implemented vs planned testing

This section answers: "How well do implemented tests compare with the planned testing?"

Plan basis:
- docs/lo2/test_inventory.csv is the authoritative list of planned tests.

Evidence:
- artifacts/plan_status.json is the mechanically generated summary.
- artifacts/junit.xml provides execution status evidence.

## Summary

- Planned tests (from LO2 inventory): 28
- Implemented tests discovered: 28
- Passing: 28
- Failing: 0
- Skipped: 0
- Deferred: 0

## Table: planned vs implemented

Columns:
- Planned Test ID: from docs/lo2/test_inventory.csv
- Level: unit / integration / system / performance / review
- Planned technique: EP/BVA, CLI contract, invariants, etc.
- Linked requirements: LO1 requirement IDs
- Implemented? Y/N
- Location: tests/path.py::test_name (or multiple when applicable)
- Status: PASS / FAIL / SKIP / XFAIL / DEFERRED
- Notes: defect reference, rationale, or follow-up action

| Planned Test ID | Level | Technique | Linked reqs | Implemented | Location | Status | Notes |
|---|---|---|---|---|---|---|---|
| T-SYS-PLACE-001 | system | CLI contract | R-FUNC-PLACE-01 | Y | tests/system/test_cli_contracts.py::test_T_SYS_PLACE_001_cli_place_success | PASS | — |
| T-INT-PLACE-001 | integration | DB boundary | R-FUNC-PLACE-01 | Y | tests/integration/test_repository_integration.py::test_T_INT_PLACE_001_service_persists_order | PASS | — |
| T-UNIT-PARSER-001 | unit | EP/BVA | R-FUNC-PLACE-01, R-ROBUST-PARSER-01 | Y | tests/unit/test_parser.py::test_T_UNIT_PARSER_001_accepts_valid_partitions; tests/property/test_parser_properties.py::test_T_UNIT_PARSER_001_valid_messages_are_parsed | PASS | — |
| T-UNIT-VALID-001 | unit | EP/BVA | R-FUNC-PLACE-01 | Y | tests/unit/test_validation.py::test_T_UNIT_VALID_001_validations_accept_valid_inputs | PASS | — |
| T-UNIT-VALID-002 | unit | EP/BVA | R-ROBUST-MOBILE-01 | Y | tests/unit/test_validation.py::test_T_UNIT_VALID_002_mobile_boundaries | PASS | — |
| T-UNIT-VALID-003 | unit | EP/BVA | R-ROBUST-MSG-01 | Y | tests/unit/test_validation.py::test_T_UNIT_VALID_003_message_length_boundaries | PASS | — |
| T-SYS-ERRCODES-001 | system | CLI contract | R-ROBUST-MOBILE-01 | Y | tests/system/test_cli_contracts.py::test_T_SYS_ERRCODES_001_invalid_mobile_exit_2 | PASS | — |
| T-SYS-ERRCODES-002 | system | CLI contract | R-ROBUST-MSG-01 | Y | tests/system/test_cli_contracts.py::test_T_SYS_ERRCODES_002_message_too_long_exit_2 | PASS | — |
| T-SYS-LIST-001 | system | CLI contract | R-FUNC-LIST-01 | Y | tests/system/test_cli_contracts.py::test_T_SYS_LIST_001_list_returns_outstanding | PASS | — |
| T-INT-LIST-001 | integration | DB query semantics | R-FUNC-LIST-01 | Y | tests/integration/test_repository_integration.py::test_T_INT_LIST_001_grouped_outstanding_orders | PASS | — |
| T-SYS-SHOW-001 | system | CLI contract | R-FUNC-SHOW-01 | Y | tests/system/test_cli_contracts.py::test_T_SYS_SHOW_001_show_returns_order_or_not_found | PASS | — |
| T-INT-SHOW-001 | integration | DB boundary | R-FUNC-SHOW-01 | Y | tests/integration/test_repository_integration.py::test_T_INT_SHOW_001_retrieves_stored_order | PASS | — |
| T-SYS-BATCH-001 | system | streaming output | R-FUNC-BATCH-01 | Y | tests/system/test_cli_contracts.py::test_T_SYS_BATCH_001_batch_emits_lines_and_summary | PASS | — |
| T-SYS-BATCH-002 | system | error partitions | R-FUNC-BATCH-01 | Y | tests/system/test_cli_contracts.py::test_T_SYS_BATCH_002_batch_malformed_lines | PASS | — |
| T-INT-FULFILL-001 | integration | state invariant | R-SAFE-FULFILL-01 | Y | tests/integration/test_repository_integration.py::test_T_INT_FULFILL_001_wrong_auth_no_transition | PASS | — |
| T-SYS-FULFILL-001 | system | CLI contract | R-SAFE-FULFILL-01 | Y | tests/system/test_cli_contracts.py::test_T_SYS_FULFILL_001_bad_auth_exit_3 | PASS | — |
| T-INT-FULFILL-002 | integration | idempotence | R-SAFE-IDEMPOTENT-01 | Y | tests/integration/test_repository_integration.py::test_T_INT_FULFILL_002_second_fulfill_rejected | PASS | — |
| T-SYS-LIVE-001 | system | timeout harness | R-LIVE-CLI-01 | Y | tests/system/test_cli_contracts.py::test_T_SYS_LIVE_001_cli_returns_within_time | PASS | — |
| T-UNIT-PARSER-002 | unit | negative tests | R-ROBUST-PARSER-01 | Y | tests/unit/test_parser.py::test_T_UNIT_PARSER_002_rejects_invalid_syntax | PASS | — |
| T-UNIT-PARSER-003 | unit | boundary tests | R-ROBUST-PARSER-01 | Y | tests/unit/test_parser.py::test_T_UNIT_PARSER_003_enforces_boundaries | PASS | — |
| T-INT-SEC-001 | integration | malicious strings | R-SEC-INJECTION-01 | Y | tests/integration/test_repository_integration.py::test_T_INT_SEC_001_sql_injection_input_no_schema_change | PASS | — |
| T-REVIEW-SEC-001 | review | inspection | R-SEC-INJECTION-01 | Y | tests/review/test_review_checks.py::test_T_REVIEW_SEC_001_sql_uses_parameters | PASS | — |
| T-INT-DB-FAIL-001 | integration | fault injection | R-ROBUST-DBFAIL-01 | Y | tests/integration/test_repository_integration.py::test_T_INT_DB_FAIL_001_database_error_no_partial_writes | PASS | — |
| T-PERF-PLACE-001 | system | repeated sampling | R-PERF-PLACE-01 | Y | tests/performance/test_performance_smoke.py::test_T_PERF_PLACE_001_place_smoke | PASS | — |
| T-PERF-BATCH-001 | system | throughput sampling | R-PERF-BATCH-01 | Y | tests/performance/test_performance_smoke.py::test_T_PERF_BATCH_001_batch_smoke | PASS | — |
| T-SYS-OUTPUT-001 | system | golden output | R-QUAL-DETERMINISM-01 | Y | tests/system/test_cli_contracts.py::test_T_SYS_OUTPUT_001_stdout_deterministic | PASS | — |
| T-REVIEW-ARCH-001 | review | inspection | R-QUAL-TESTABILITY-01 | Y | tests/review/test_review_checks.py::test_T_REVIEW_ARCH_001_testability_seams_exist | PASS | — |
| T-SYS-METRICS-001 | system | contract test | R-QUAL-VISIBILITY-01 | Y | tests/system/test_cli_contracts.py::test_T_SYS_METRICS_001_metrics_schema_and_reset | PASS | — |

## Notes on deviations from plan

For any deviation from the LO2 plan, record:
- What changed and why (risk discovery, constraints, reprioritisation)
- Whether the deviation weakens adequacy and how it will be mitigated
- Whether the change will be reflected back into LO2 docs (if appropriate)

No deviations were observed in the current evidence run; all planned
LO2 test IDs were implemented and passing.
