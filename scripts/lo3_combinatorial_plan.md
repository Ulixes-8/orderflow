# LO3 Combinatorial Plan — Category-Partition + Full Cross-Product

Purpose:
- Define categories and choices for systematic combinatorial testing.
- Define constraints to prevent invalid/uninteresting combinations.

## Categories (LO3 evidence subset)
- mobile_class: valid, missing_plus, too_short, too_long, non_digit
- message_class: valid, invalid_prefix, unknown_sku, qty_zero, qty_too_large, too_many_items
- auth_class: correct, incorrect

LO3 enumerates the full cross-product only over the bounded subset above
(mobile_class × message_class × auth_class), producing 60 deterministic cases.

## Constraints (examples)
- Avoid generating combinations that cannot occur given command semantics.

## Future extension (not used in LO3 evidence)
- db_state_class: empty, has_pending, has_fulfilled
- If message_class != valid, db_state_class constraints may be irrelevant for place.
- For fulfill, require db_state_class in {has_pending, has_fulfilled}.
- If added, document the expanded cross-product and any additional constraints.

## Coverage criteria
- Category coverage: each choice used at least once
- Pairwise coverage reported as an adequacy metric within a bounded subset
  (e.g., mobile_class x message_class x auth_class), even when the full
  cross-product is enumerated because the space is small and bounded.
