# Evaluation of test plan quality (LO2)

## Strengths (why the plan is adequate)
- Direct derivation from LO1 test basis and traceability (minimises drift).
- Explicit multi-level strategy: unit/integration/system/performance.
- Explicit out-of-scope items are documented (audit-friendly).
- Risk-driven prioritisation: P0 first, then P1/P2.

## Weaknesses / vulnerabilities (what might be missing)
- Concurrency is not addressed (declared out-of-scope).
- Security is sampled, not proven (negative testing limits acknowledged).
- Performance is noisy and environment-dependent (mitigated later by LO4 stats).

## Omissions and mitigation actions
- If auditors expect stronger DB-failure proof, we will add fault injection using a
  repository wrapper that simulates mid-transaction failures (planned as LO3/LO4 evidence).
- If determinism flakiness is observed, enforce stable ordering at the boundary and
  isolate time/ID sources in tests (seams already exist).
