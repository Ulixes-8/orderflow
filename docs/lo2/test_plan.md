# Test Plan (LO2) — OrderFlow
(ISO/IEC 29119-2/29119-3 inspired structure; sized for coursework auditability)

## 1. Plan identifier and purpose
- Plan ID: TP-ORDERFLOW-LO2-v1
- Purpose: Provide a structured, evolving test plan that delivers adequate assurance
  for LO1 requirements, using a mix of unit/integration/system/performance strategies.

## 2. References (test basis)
This plan is derived directly from LO1 artefacts:
- Requirements catalogue: `docs/lo1/requirements.json`
- Approach mapping: `docs/lo1/test-approach.md`
- Traceability: `docs/lo1/traceability.csv` (requirement → planned test IDs)
The plan should be considered invalid if it diverges from those artefacts.

## 3. Scope
### 3.1 In scope (test items)
- CLI boundary (`orderflow`): contract, exit codes, stdout JSON determinism
- Service layer (`OrderService`): business rules, state transitions, error mapping
- Parsers/validators: grammar, limits, boundary conditions, equivalence partitions
- Persistence boundary: SQLite repository semantics, parameterization, failure behaviour
- Observability: metrics and diagnostics instrumentation

### 3.2 Out of scope (explicitly)
- Concurrency/parallel access correctness (single-process model for coursework)
- Networked APIs (not present)
- UI/UX beyond contract-level error messaging

## 4. Test strategy overview (levels + techniques)
Aligned with LO1:
- Unit: EP/BVA + negative tests for parser/validation partitions.
- Integration: repository boundary + state invariants (auth, idempotence, DB failure).
- System: CLI end-to-end, output contract, exit codes, batch stream correctness.
- Performance: repeated sampling with summary statistics (formalised in LO4).

Cross-cutting:
- Regression stability via deterministic JSON output.
- Scaffolding: deterministic clock/id-generator seams already present for isolation.

## 5. Entry/exit criteria
### Entry (per suite)
- Unit suite: module imports + deterministic dependencies available.
- Integration suite: SQLite temp DB created; schema initialised.
- System suite: CLI installed/accessible; temp working directory available.

### Exit (adequacy gates; enforced later by CI/LO5)
- All tests passing.
- Coverage thresholds and test-yield targets defined in LO3/LO4 evidence.
- Traceability consistency: every highlighted LO1 requirement has at least one
  implemented test ID (progressively satisfied as the test set evolves).

## 6. Suspension/resumption criteria
Suspend:
- Any nondeterministic/flaky test observed in ≥2 consecutive runs.
- Any instrumentation that contaminates stdout contract (must be fixed immediately).

Resume:
- Root cause documented + test rewritten (better oracle, isolation, or removed).

## 7. Test deliverables
- Test code (pytest), fixtures/scaffolding, and test data (golden files where needed).
- Coverage reports (line/branch), and later mutation/fuzz evidence (LO3).
- Performance sampling scripts and summary outputs (LO4).
- Reviews/inspection evidence and CI configuration (LO5).

## 8. Risks, omissions, and mitigations (audit-friendly)
- Risk: performance noise → Mitigation: repeated sampling + variance reporting (LO4).
- Risk: security “proof” impossible via sampling → Mitigation: combine malicious-string
  tests with code review of SQL parameterization (LO5 review evidence).
- Risk: missing concurrency bugs → Mitigation: explicitly out-of-scope; documented.

## 9. Responsibilities and schedule (coursework sized)
Single-developer roles still documented (ISO style):
- Test designer: maintains `docs/lo2/test_inventory.csv` and updates plan evolution.
- Test implementer: writes tests in priority order (P0 → P1 → P2).
- Reviewer: conducts checklist reviews on plan + instrumentation + critical code paths.

Schedule: incremental, requirement-driven (TDD): implement smallest test set that
forces correct behaviour; extend as new risks/requirements are considered.
