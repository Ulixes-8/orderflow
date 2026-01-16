# LO5.1 Review Criteria Checklist

This checklist defines the criteria used in the LO5.1 code review. Each item
states what is checked and why it matters for the Orderflow CLI’s correctness,
robustness, and maintainability.

## Correctness & invariants

- [ ] Validate that domain invariants are enforced at module boundaries.
  This checks that input parsing and state transitions preserve expected
  invariants. It matters because silent invariant drift can corrupt downstream
  results and break CLI contracts.
- [ ] Confirm that state changes are atomic from the user’s perspective.
  This checks that partial writes do not leave the system in a conflicting
  state. It matters because partial writes can break correctness and user
  expectations.

## Robustness & error handling

- [ ] Ensure error paths map to documented failure modes.
  This checks that exceptions are converted into stable error codes or messages.
  It matters because users and tests depend on predictable failure behavior.
- [ ] Identify missing or weak failure-mode seams.
  This checks whether failure scenarios can be triggered in tests. It matters
  because untestable failure paths often regress unnoticed.

## Security (SQL usage and injection resistance)

- [ ] Validate that SQL is parameterized.
  This checks that SQL statements use bound parameters rather than string
  formatting. It matters because string interpolation enables injection risks.
- [ ] Verify that SQL query construction avoids unsafe string composition.
  This checks for `.format()` or f-strings in SQL definitions. It matters
  because dynamic SQL composition can bypass protections.

## Determinism & contract adherence (stdout JSON, ordering)

- [ ] Confirm stdout contains only contract JSON payloads.
  This checks that diagnostics are separated from stdout. It matters because
  extra output breaks parsers and contract tests.
- [ ] Validate deterministic ordering of outputs.
  This checks that list ordering is explicit and stable. It matters because
  nondeterminism undermines reproducibility and testing.

## Testability & seams (dependency injection, fault injection points)

- [ ] Identify explicit seams for database failure injection.
  This checks for dependency injection points or toggles. It matters because
  testability of database errors is required by LO4/LO5 evidence.
- [ ] Identify explicit seams for internal error injection.
  This checks for hooks that can force internal failures. It matters because
  unexercised internal failures are a recurring weakness.

## Maintainability (complexity, duplication, cohesion)

- [ ] Flag complex or duplicated logic that lacks documentation.
  This checks for repeated patterns without abstraction. It matters because
  duplication increases maintenance risk and inconsistent behavior.
- [ ] Confirm cohesion between modules and responsibilities.
  This checks for single-purpose modules and clear interfaces. It matters
  because blurred boundaries complicate changes and reviews.

## Observability (diagnostics separation from stdout)

- [ ] Ensure diagnostics are logged to stderr or log channels only.
  This checks that stdout remains reserved for contract output. It matters
  because diagnostics must not corrupt CLI contract output.
