# Requirements for OrderFlow (LO1)

This is a human-readable view of `requirements.json` (source of truth).
It is structured by **type** to demonstrate requirement diversity, as recommended
in the LO1 tutorial and requirements discussion session materials.

## 0. Stakeholders (used to drive requirement diversity)
We identify multiple stakeholders and derive 1–3 requirements per stakeholder to
ensure diversity across concerns (not only the primary user):
- Customer (places orders): correctness, responsiveness, clear errors
- Operations staff (fulfills orders): safety of state transitions, correctness of listings
- System owner / admin: robustness, security, diagnosability (metrics), recovery on failures
- Developer / maintainer: testability, determinism, modular design

This stakeholder-driven approach is explicitly suggested for LO1.

---

## 1. Functional correctness (what the system does)
- R-FUNC-PLACE-01 (P0, System): valid place creates correct PENDING order.
- R-FUNC-LIST-01 (P0, System): list shows only outstanding PENDING orders grouped by mobile.
- R-FUNC-SHOW-01 (P0, System): show returns full order or ORDER_NOT_FOUND.
- R-FUNC-BATCH-01 (P1, System): batch emits per-line JSON + final summary.

## 2. Safety (bad things never happen)
- R-SAFE-FULFILL-01 (P0, Integration): unauthorized fulfill cannot change persisted state.
- R-SAFE-IDEMPOTENT-01 (P1, Integration): fulfilling twice is rejected and does not modify.

## 3. Liveness (system returns to a ready state / completes)
- R-LIVE-CLI-01 (P1, System): CLI always returns a response and exits for finite input.

## 4. Robustness and security (degraded but safe behavior under stress/malicious input)
- R-ROBUST-MOBILE-01 (P0, Unit): invalid mobile rejected; no side effects.
- R-ROBUST-MSG-01 (P0, Unit): too-long message rejected; no side effects.
- R-ROBUST-PARSER-01 (P0, Unit): grammar + limits enforced (tokens/items/qty).
- R-SEC-INJECTION-01 (P1, Integration): persistence not vulnerable to injection.
- R-ROBUST-DBFAIL-01 (P1, Integration): DB errors yield DATABASE_ERROR without inconsistent partial writes.

## 5. Measurable quality attributes (verifiable quantitative properties)
- R-PERF-PLACE-01 (P2, System): explicit latency targets for place under defined workload.
- R-PERF-BATCH-01 (P2, System): throughput measured/reported under defined workload.

## 6. Qualitative requirements (“-ilities” and test-relevant qualities)
- R-QUAL-DETERMINISM-01 (P1, System): deterministic JSON output for regression stability.
- R-QUAL-TESTABILITY-01 (P1, Unit): modularity and dependency injection support isolation.
- R-QUAL-VISIBILITY-01 (P1, System): metrics provide operational visibility.

---

## 7. Portfolio highlight set (small number, maximally distinct)
The LO1 tutorial notes the portfolio should mention a small set of distinct requirements,
while pointing to a short repo document listing the full set. We will highlight:

1) R-FUNC-PLACE-01 (functional correctness)
2) R-SAFE-FULFILL-01 (safety: unauthorized state change prevented)
3) R-ROBUST-PARSER-01 (robustness: boundary/grammar constraints)
4) R-SEC-INJECTION-01 (security: injection resistance)
5) R-PERF-PLACE-01 (measurable QA: performance)
6) R-QUAL-DETERMINISM-01 (qualitative: determinism / testability enabler)

Each is designed to “force” a different test approach and demonstrates diversity.
