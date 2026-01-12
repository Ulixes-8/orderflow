# Test Basis and Test Model (LO1) — ISO/IEC 29119 Inspired

The LO1 tutorial suggests thinking in terms of a **test basis** and
**required behaviour**, key elements used to define a test model.

## 1. Test basis
Primary test basis artefacts:
- `docs/lo1/requirements.json` (canonical requirements set)
- CLI contract as specified in README/help text (system boundary)
- Source code modules for unit-level required behaviours:
  - validation rules (formats)
  - parser grammar/limits
  - service state transitions
  - SQLite persistence semantics

## 2. Required behaviour (selected examples)
We define required behaviour in a way that can be checked by tests:
- If auth is incorrect, fulfill must not change order state (R-SAFE-FULFILL-01).
- If message contains > max tokens, parsing fails with TOO_MANY_ITEMS (R-ROBUST-PARSER-01).
- JSON outputs are deterministic (R-QUAL-DETERMINISM-01).

## 3. Test model overview
### 3.1 Test items
- CLI (`orderflow`) as system under test
- Service layer as integration target
- Parser/validation functions as unit targets
- SQLite repository as integration target

### 3.2 Test conditions (derived by partitioning)
We derive test conditions by partitioning input and state space:

#### Mobile number partition (R-ROBUST-MOBILE-01)
- Valid E.164: "+447700900123"
- Missing plus: "447700900123"
- Too short/too long
- Leading zero after plus
- Non-digit characters

#### Message grammar partition (R-ROBUST-PARSER-01)
- Missing ORDER keyword
- ORDER with zero items
- Single SKU, SKU=QTY, mixed case
- Invalid SKU token formats
- Qty boundaries: 0, 1, 99, 100, leading zeros
- Too many items
- Duplicate SKUs with aggregation overflow

#### State partition (R-SAFE-FULFILL-01 / R-SAFE-IDEMPOTENT-01)
- PENDING order
- FULFILLED order
- Missing order_id
- Auth code correct/incorrect/invalid format

### 3.3 Coverage targets (LO1-level)
At LO1, we define *what coverage means* (not yet compute it):
- Requirement type coverage: each major type has at least one requirement + planned tests.
- Requirement level coverage: system/integration/unit requirements are present.
- Technique coverage: multiple approaches are identified (unit, integration, system, statistical/perf).

Traceability to planned tests is captured in `traceability.csv`.
