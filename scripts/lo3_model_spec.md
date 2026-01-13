# LO3 Model Spec (FSM) — OrderFlow (template)

Purpose:
- Define a minimal behavioral model for model-based testing (FSM).
- Measure state and transition coverage as LO3 evaluation criteria.

## States
- S0: No order exists for a mobile
- S1: Pending order exists
- S2: Fulfilled order exists

## Transitions (examples)
- place: S0 -> S1
- show: S1 -> S1 (returns order)
- list: S1 -> S1 (includes order)
- fulfill(auth ok): S1 -> S2
- fulfill(auth bad): S1 -> S1 (UNAUTHORIZED)
- fulfill on S2: S2 -> S2 (ORDER_ALREADY_FULFILLED)
- show missing: S0 -> S0 (ORDER_NOT_FOUND)

## Coverage criteria
- State coverage: visited states / defined states
- Transition coverage: visited transitions / defined transitions

Document omissions explicitly (what the model does not attempt to cover).
