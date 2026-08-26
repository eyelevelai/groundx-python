## Context

`custom_outputs.py` currently normalizes relationship strings in
`_relationship_comparison_value()` and repeated-record identity strings in
`_normalize_match_value()`. Advanced identity paths can bypass normalization
through `identity_match.exact_attrs`. `select_relationship_parent()` uses the
relationship branch directly.

The current selector already preserves populated-key shape, nonstring type
rules, and stable parent order. The new comparison must change only string
equality. It must not change record admission, threshold counts, missing-value
rules, conflict evidence, merge behavior, selection order, or output values.

The code lives under `src/groundx/extract/`, tests under `tests/extract/`, and
OpenSpec under `openspec/`. All three are protected by `.fernignore` and survive
Fern regeneration.

## Goals / Non-Goals

**Goals:**

- One reusable key function owns string transformation.
- One equality wrapper delegates to that key function.
- Every identity or relationship string key uses the same behavior.
- Existing nonstring, absence, threshold, and stable-order behavior remains.
- Raw values never change.

**Non-Goals:**

- No value normalization, repair, display change, or new workflow metadata.
- No matching profile, exact mode, field switch, customer branch, or caller
  option.
- No Unicode spoof-detection library, fuzzy matching, edit distance, or mapping
  beyond `{0, o}`, `{1, i, l}`, and `{8, b}`.
- No use in scalar candidate evidence dedupe, route or schema identity, sorting,
  rendering, serialization, logging, or arbitrary equality.
- No existing test or fixture change without human approval.

## Decisions

### Two small public functions own string matching

`match_key(value: str) -> str` transforms one string.
`values_match(left: str, right: str) -> bool` compares only
`match_key(left)` and `match_key(right)`. Both reject nonstring input and contain
no nonstring comparison semantics or second transformation.

For a string, `match_key` performs one linear pass after `casefold()`:

1. Remove every character for which `str.isspace()` is true.
2. Map `o` to `0`, `i` and `l` to `1`, and `b` to `8`.
3. Preserve every other character and the resulting length.

Whitespace-only strings remain absent where the existing caller already treats
them as absent. Callers unwrap values and select their existing number, boolean,
mapping, list, extracted-field wrapper, absence, and unsupported-type behavior
before invoking either function. Callers that need hashable structured keys
retain their current typed wrappers and call `match_key` only for string
components. This prevents Python equality such as `True == 1` from becoming
matcher behavior.

This restricted implementation is safer than an open-source Unicode skeleton
library. Unicode security libraries create many equivalences that were not
approved for extraction matching.

### Custom-output identity and relationships share the functions

`custom_outputs.py` uses `match_key` for string components created by
`_identity_index_value()`, `_identity_key()`,
`_identity_partition_key()`, `_identity_comparison_value()`, and
`_records_share_identity()`. Direct string equality uses `values_match`.

`select_relationship_parent()` uses the same equality while retaining the
existing child populated-key filter, exact populated-key shape requirement, and
first matching parent in stable input order.

`identity_match.exact_attrs` remains accepted by workflow preparation and
readback for compatibility, but cannot select raw string equality. Removing the
runtime branch avoids Cashbot or workflow migration work.

### Comparison never becomes output

Comparison values exist only inside lookups and comparisons. The first raw
record and existing merge rules continue to determine retained fields,
conflicts, provenance, diagnostics, and final output.

### Regression gates protect behavior and false merges

New tests cover case, every whitespace form, each approved class, combined
differences, punctuation, unmapped characters, unequal lengths, whitespace-only
values, nonstring helper rejection, existing caller behavior for mixed and
nonstring values, structured identity values, stable parent order, populated-key
shape, raw-value retention, and `exact_attrs` no-op behavior.

Existing tests run unchanged. If an existing assertion fails because the new
equality is intentional, implementation stops before editing it and records the
input, old result, new result, and downstream effect for human approval.

Before release, the Internal Arcadia consumer change runs a read-only collision
report over protected fixtures and representative private captures. It lists
each pair of distinct raw strings that produces one key, with caller and field.
Every unexpected collision requires human approval. The report is not a runtime
mode and does not mutate or commit private input.

The docs-only `eyelevel-fern-config`
`document-universal-identifier-matching` change must merge before the SDK
release. It removes the public promise that `exact_attrs` selects exact runtime
equality and documents the universal comparison without changing the API schema,
compiler, or workflow payload.

## Risks / Trade-offs

- Distinct identifiers such as `IO` and `10` can collapse. The collision report
  and human gate block release on unexpected cases.
- Universal equality intentionally supersedes legacy `exact_attrs` behavior.
  Existing metadata remains readable, avoiding a workflow migration.
- GroundX Python cannot publish itself. The PR ends with a human release handoff
  naming the merged commit and requested version.

## Migration Plan

1. Implement and validate the GroundX Python functions and production callers.
2. Exercise the Internal Arcadia implementation against this branch and run its
   collision report before publishing.
3. Obtain approval for every unexpected collision and any existing-test change.
4. Merge the Fern public-documentation change.
5. Merge GroundX Python and hand the merged commit and requested version to the
   human release owner.
6. Pin the published version in Internal Arcadia, rebuild its image, and run the
   protected and affected-document verification.

Rollback pins the prior SDK release and restores the prior Internal Arcadia
image. No stored value changes.

## Open Questions

None.
