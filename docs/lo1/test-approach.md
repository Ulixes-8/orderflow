# Test Approach (LO1)

## 0. Why multiple approaches are necessary
No single technique is sufficient for all purposes: requirements differ in what is
observable, what oracles exist, and what risks dominate. Our approach follows the
A&T principle of **redundancy/diversity**: use different methods to obtain
independent reassurance.

## 1. A&T principles applied (explicit)
- Partition: we partition requirements by type and inputs by equivalence classes.
- Visibility: requirements are structured and traceable; metrics improve observability.
- Feedback: early test thinking can reveal specification gaps; we revise requirements.
- Restriction: we prefer verifiable requirements (explicit bounds) to vague statements.
- Sensitivity: we prefer criteria where failing one representative test implies failure
  across a partition (boundary-driven parser tests are high sensitivity).
- Redundancy/diversity: we pair unit + integration + system tests for key requirements.

## 2. Requirement → test approach mapping (examples)
| Requirement | Level(s) | Primary approach | Secondary approach | Rationale |
|---|---|---|---|---|
| R-FUNC-PLACE-01 | System+Int+Unit | End-to-end CLI tests | Unit tests for parser/validation | System ensures contract; unit gives diagnostic precision. |
| R-SAFE-FULFILL-01 | Integration+System | Integration state-invariant tests | System tests for error codes | Safety requires persisted state checks. |
| R-ROBUST-PARSER-01 | Unit | EP/BVA + negative tests | Property-based later (LO3) | Parser rules are best tested as pure functions. |
| R-SEC-INJECTION-01 | Integration | DB-backed malicious strings | Static inspection of SQL usage | Injection risk exists at persistence boundary. |
| R-PERF-PLACE-01 | System | Repeated sampling + summary stats | Compare cold vs warm DB | Perf is noisy; multiple samples reduce variance. |
| R-QUAL-DETERMINISM-01 | System | Golden output regression | Snapshot-based checks | Prevent flaky regression tests and hidden nondeterminism. |

## 3. Traceability
Planned tests are recorded in `traceability.csv` (test IDs used later in LO2/LO3).
