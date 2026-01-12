# LO1 Evidence Pack — Requirements → Testing Strategy

This folder contains the evidence referenced by the portfolio for:

LO1: Analyze requirements to determine appropriate testing strategies.

The LO1 tutorial emphasizes:
- requirements diversity across types (functional + safety/correctness/liveness +
  security/robustness + measurable attributes + “-ilities”),
- requirements spanning different levels (system/integration/unit),
- early identification of test approaches and their limitations,
- and keeping the portfolio discussion small by pointing to a short repo document.
(See LO1 tutorial notes.)

## Contents
- requirements.json
  Structured “source of truth” requirements catalogue, tagged by:
  type, level, stakeholder, priority, and verifiability.
- requirements.md
  Human-readable view of the requirements, grouped by type (partitioning).
- levels.md
  Requirement level analysis (system / integration / unit).
- test-model.md
  ISO/IEC 29119-inspired test basis + required behaviour + test conditions.
- test-approach.md
  Requirement → technique mapping (unit/integration/system + method choice).
- appropriateness.md
  Why these test choices fit, and what they cannot prove.
- traceability.csv
  Links requirements → planned test IDs (used later in LO2/LO3).

## “Beyond taught” (small but useful)
- scripts/validate_lo1.py
  A lightweight static checker that validates requirement IDs/types/levels and
  cross-checks traceability entries, improving process visibility.
