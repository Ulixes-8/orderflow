# Requirement Levels (System / Integration / Unit)

## 0. Why levels matter (verification vs validation)
Verification asks: “does the system meet the stated requirements?”
Validation asks: “does the system meet users’ real needs?”
For LO1 we primarily structure a **verifiable** test basis (verification), while
noting where validation considerations influence requirement choice (e.g., usability).

We also intentionally reframe requirements to be verifiable where possible
(e.g., using explicit bounds rather than vague “soon”), reflecting the course
discussion on verifiable vs merely validatable specs.

## 1. System decomposition (levels)
- System boundary: CLI commands and output contracts.
- Integration: service + repository + schema/transactions.
- Unit/component: parser, validation, deterministic computations and formatting.

## 2. Level assignment table
| Requirement ID | Primary level | Supporting levels | Why this assignment is necessary |
|---|---|---|---|
| R-FUNC-PLACE-01 | System | Unit, Integration | System ensures CLI contract; unit isolates parsing/validation; integration ensures persistence invariants. |
| R-SAFE-FULFILL-01 | Integration | System | Safety depends on persisted state, not just return codes. |
| R-ROBUST-PARSER-01 | Unit | — | Grammar/limits are best tested as pure functions; fast and diagnostic. |
| R-SEC-INJECTION-01 | Integration | System | Injection risk is realized at persistence boundary; requires DB-backed evidence. |
| R-PERF-PLACE-01 | System | — | Performance is end-to-end; unit tests are insufficient proxies. |
| R-QUAL-DETERMINISM-01 | System | — | Determinism is observable at the output boundary. |

(Full mapping is in requirements.json; this table is the explanatory rationale.)
