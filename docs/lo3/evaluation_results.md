# LO3.4 Evaluation of results (apply criteria and interpret)

This section applies the criteria defined in evaluation_criteria.md and
communicates what the results mean, including limitations and next steps.

## A) Requirements coverage evaluation
Metric results:
- % requirements covered by >= 1 passing test: <...>%
- Highlight requirements covered by system/integration tests: <...>%

Interpretation:
- What remains uncovered, and why?
- Are uncovered requirements deferred, out-of-scope, or missing tests?
- What is the mitigation plan?

## B) Structural coverage evaluation (line + branch)
Metric results:
- Overall core-module line coverage: <...>%
- Overall core-module branch coverage: <...>%

Interpretation:
- List meaningful uncovered regions and whether they indicate test gaps.
- Justify any exclusions (unreachable, defensive, platform constraints).
- Explain how oracle strength is ensured (not just "covered").

## C) Combinatorial evaluation
Metric results:
- Category coverage: <...>%
- Pairwise coverage (bounded subset): <...>%

Interpretation:
- Which interactions were targeted and why?
- Any constrained/forbidden combinations and rationale?
- Any failures found due to interaction effects (yield)?

## D) Model-based evaluation
Metric results:
- State coverage: <...>%
- Transition coverage: <...>%

Interpretation:
- Which transitions are most critical (safety/liveness)?
- Any missing transitions and whether they matter?
- How does the model complement the functional/contract tests?

## E) Yield evaluation
Metric results:
- Defect yield per technique: <table>
- Error-code yield: <...> distinct codes exercised

Interpretation:
- Which techniques were most effective and why?
- What does a low yield mean at this stage (quality vs weak tests)?
- How are discovered defects prevented from regressing (new tests)?

## Performance note (LO3 vs LO4)
LO3 includes baseline smoke evidence only.
Formal statistical characterization and target evaluation occur in LO4.

