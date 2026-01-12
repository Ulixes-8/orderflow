# Test Plan (LO2) — OrderFlow
(ISO/IEC 29119-2/29119-3 inspired structure; sized for coursework auditability)

## 1. Plan identifier and purpose
- Plan ID: TP-ORDERFLOW-LO2-v1
- Purpose: Provide a structured, evolving test plan that delivers adequate assurance for LO1 requirements,
  using a mix of unit/integration/system/performance strategies, and explicitly documenting omissions/risks.

## 2. References (test basis)
This plan is derived directly from LO1 artefacts (the test basis):
- Requirements catalogue: `docs/lo1/requirements.json`
- Approach mapping: `docs/lo1/test-approach.md`
- Traceability: `docs/lo1/traceability.csv` (requirement → planned test IDs)

Contract basis for system tests:
- CLI contract: `docs/cli_contract.md`

The plan should be considered invalid if it diverges from the LO1 test basis artefacts above.

## 3. Context, scope, and constraints
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

### 3.3 Assumptions and constraints (audit explicit)
- Single-developer coursework constraints: limited time, limited environments.
- System is exercised via CLI + in-process service/repository.
- Performance evidence is statistical (sampling) and environment-dependent.

### 3.4 Stakeholders (aligned to LO1)
- Customer: correctness and clear errors for `place`
- Operations: safe fulfilment and correct listing/show workflows
- System owner/admin: robustness, security at DB boundary, diagnosability/metrics
- Developer/maintainer: determinism, modularity/testability, fast regression

## 4. Planning process and lifecycle placement (TDD / iterative)
Testing is planned and evolved iteratively:
1) Start from LO1 requirements + traceability IDs.
2) Add/adjust tests when new requirements, risks, or gaps are discovered.
3) Maintain inventory (`docs/lo2/test_inventory.csv`) as the authoritative plan for “what tests exist/planned”.

Lifecycle placement (what happens when):
- During implementation: unit tests (parser/validation) are created first for fast feedback.
- When persistence is integrated: integration tests validate DB boundaries and invariants.
- When CLI contract is stable: system tests validate stdout JSON schemas + exit codes + determinism.
- After functional stability: performance sampling scripts produce statistical summaries (formalised in LO4).

## 5. Test strategy overview (levels + techniques)
Aligned with LO1 requirement→approach mapping:
- Unit: EP/BVA + negative tests for parser/validation partitions.
- Integration: repository boundary + state invariants (auth, idempotence, DB failure, injection-style strings).
- System: CLI end-to-end, output contract, exit codes, batch stream correctness, golden determinism.
- Performance: repeated sampling with summary statistics (formalised in LO4).

## 6. Instrumentation/scaffolding plan (to improve adequacy)
Instrumentation is used to improve observability without breaking the CLI contract:
- Diagnostics sink (optional; file-only; off by default): enabled via `--diagnostics` or `ORDERFLOW_DIAGNOSTICS_PATH`.
- Invariant checks in service layer act as an internal-consistency oracle (surfaced as INTERNAL_ERROR).
- Existing metrics counters + timing series support performance sampling and regression triage.

Authoritative detail: `docs/lo2/instrumentation.md`.

## 7. Entry/exit criteria
### Entry (per suite)
- Unit suite: module imports + deterministic dependencies available.
- Integration suite: SQLite temp DB created; schema initialised.
- System suite: CLI installed/accessible; temp working directory available.

### Exit (adequacy gates; enforced later by CI/LO5)
- All implemented tests passing.
- Traceability consistency: every LO1 requirement has ≥1 planned test in inventory; highlighted LO1 requirements
  have ≥1 implemented test as the suite evolves.
- No stdout contract contamination: stdout remains deterministic JSON (or documented exceptions such as list --format lines).

## 8. Suspension/resumption criteria
Suspend:
- Any nondeterministic/flaky test observed in ≥2 consecutive runs.
- Any instrumentation that contaminates stdout contract.

Resume:
- Root cause documented + test rewritten (better oracle, better isolation, or removed).

## 9. Test deliverables
- Test code (pytest), fixtures/scaffolding, and test data (golden files where needed).
- Coverage reports, and later mutation/fuzz evidence (LO3).
- Performance sampling scripts and summary outputs (LO4).
- Reviews/inspection evidence and CI configuration (LO5).

## 10. Risks, omissions, and mitigations
- Risk: performance noise → Mitigation: repeated sampling + variance reporting (LO4).
- Risk: security “proof” impossible via sampling → Mitigation: combine malicious-string tests with review evidence
  of SQL parameterization.
- Risk: missing concurrency bugs → Mitigation: explicitly out-of-scope; documented.

## 11. Responsibilities and communication
Roles (single-developer, documented for audit):
- Test designer: maintains `docs/lo2/test_inventory.csv` and updates `docs/lo2/plan_evolution.md`.
- Test implementer: writes tests in priority order (P0 → P1 → P2).
- Reviewer: checklist reviews on plan + instrumentation + critical code paths.

Communication:
- Evidence is located in `docs/lo1/*` and `docs/lo2/*` with validator scripts under `scripts/`.
- CI outputs and local run logs are retained as LO5 evidence.
