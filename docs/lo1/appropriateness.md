# Appropriateness and Limitations (LO1)

## 0. Reality check: what tests can and cannot prove
Correctness properties are undecidable in general; exhaustive testing is infeasible.
Therefore we adopt a combination of techniques, each with known inaccuracies:
- Testing may miss violations (optimistic inaccuracy).
- Some analyses may reject correct programs (pessimistic inaccuracy).
Thus, selection of techniques is a trade-off, not a single best answer.

## 1. Appropriateness by requirement type

### 1.1 Functional correctness
Appropriate:
- System tests validate user-visible contracts.
- Unit tests provide high-sensitivity checks on partitions (parser/validation).
Limitations:
- System tests alone can under-diagnose faults; unit tests alone miss integration.

### 1.2 Safety (unauthorized fulfillment)
Appropriate:
- Integration tests that verify persisted state invariants before/after calls.
Limitations:
- A passing return-code test alone is insufficient; must check state.

### 1.3 Robustness/security-style
Appropriate:
- Partitioned negative testing (EP/BVA) plus DB-backed malicious-string tests.
Limitations:
- Negative testing samples; it does not prove “no vulnerabilities”.
Mitigation:
- Combine with code inspection of SQL parameterisation and later fuzz/property tests.

### 1.4 Performance (measurable QA)
Appropriate:
- Repeated sampling and summary statistics.
Limitations:
- Environment noise, machine variability, DB warm/cold effects.
Mitigation:
- Define the workload precisely; report variability and confidence intervals in LO4.

## 2. Explicit trade-offs (audit-friendly)
- We prioritise early requirement/test analysis to increase process visibility and
  detect specification gaps early, consistent with the quality-process guidance that
  testing and analysis should not be an afterthought.
- We structure requirements to be verifiable where possible by adding explicit bounds
  (restriction), rather than vague statements that are only “validatable”.
