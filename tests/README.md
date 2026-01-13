# Tests (LO3 implementation)

Conventions (for auditability):
- Encode LO2 test IDs in test function names or markers, e.g.
  test_T_SYS_ERRCODES_001_invalid_mobile_exit_2
- Keep unit/integration/system separation:
  - tests/unit/
  - tests/integration/
  - tests/system/
  - tests/property/  (Hypothesis)

Planned test IDs and techniques are defined in:
- docs/lo2/test_inventory.csv

CLI contract basis for system tests:
- docs/cli_contract.md
