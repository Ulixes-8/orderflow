# LO3 Combinatorial Plan — Category-Partition + Bounded Pairwise (template)

Purpose:
- Define categories and choices for systematic combinatorial testing.
- Define constraints to prevent invalid/uninteresting combinations.

## Categories (example)
- mobile_class: valid, missing_plus, too_short, too_long, non_digit
- message_class: valid, invalid_prefix, unknown_sku, qty_zero, qty_too_large, too_many_items
- auth_class: correct, incorrect
- db_state_class: empty, has_pending, has_fulfilled

## Constraints (examples)
- If message_class != valid, db_state_class constraints may be irrelevant for place.
- For fulfill, require db_state_class in {has_pending, has_fulfilled}.
- Avoid generating combinations that cannot occur given command semantics.

## Coverage criteria
- Category coverage: each choice used at least once
- Pairwise coverage: within a bounded subset (e.g., mobile_class x message_class x auth_class)

