# Proposal — default-first-stable-ties

## Why

`select_relationship_parent` resolves multiple exact parent candidates by the
packet's declared `multiple_match_strategy`. `first_stable` is the only legal
declared value; an absent declaration made the tie ambiguous and left the child
unmatched. The original Arcadia matcher (`Statement.get_charge_meter` on
`internal-arcadia-agents` `origin/main`) attaches the child to the first
matching parent unconditionally, so absence silently selected a behavior the
original algorithm never had. Live extraction hit this: sibling parents that
legitimately share every declared match attribute (supply and delivery meters)
sent their charges to the account level, while the governed answer keys expect
every charge nested.

Ruled by Benjamin Fletcher on 2026-08-17, superseding the
undeclared-equals-ambiguous half of ruling 7b (2026-08-05): an absent
`multiple_match_strategy` defaults to `first_stable`. The field stays on the
packet and in YAML validation for future strategy extension.

## What changes

1. `select_relationship_parent` treats an absent strategy as `first_stable` on
   multiple direct matches. An explicitly declared strategy other than
   `first_stable` still yields no selection with `ambiguous=True` (YAML
   validation continues to reject such values at authoring time).
2. The matcher docstring corrects its baseline citation: the ported legacy
   matcher is `get_charge_meter` on `origin/main`; the previously cited
   `2797b5e` is a plan-branch checkpoint, not main.
3. Behavior-table row R16 and the reassembly and seam tests flip from
   undeclared-equals-ambiguous to the `first_stable` default.
4. The promotion-time acceptance check no longer requires accepted inputs to
   declare `first_stable`; it now rejects only a foreign declared strategy.

## Impact

- Affected specs: `custom-output-readback` (tie scenarios and the exported
  primitive's `ambiguous` semantics).
- Affected code: `src/groundx/extract/custom_outputs.py`; tests
  `test_relationship_parent_selection_red.py`,
  `test_relationship_parent_selection_seam_red.py`,
  `test_custom_output_reassembly.py`.
- Consumers: undeclared ties now attach the child to the first stable parent
  instead of emitting `ambiguous_relationship_match` and leaving it unmatched.
  Workflows with genuine ties change output shape; the extraction-boundary
  capture rerun and answer keys are the verification.
