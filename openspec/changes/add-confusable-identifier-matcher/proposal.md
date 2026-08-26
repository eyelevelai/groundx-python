## Why

Identity and relationship matching still treats OCR variants such as `I` and
`1` as different values. In AGE-319, that can leave charges unattached unless a
model happens to rewrite the identifier before final parent selection.

GroundX Python also has separate string comparison branches for repeated-record
identity and relationship selection. One small comparison function should own
case, whitespace, and approved OCR-confusable handling for both.

## What Changes

- Add public string-only `match_key(value: str) -> str` and
  `values_match(left: str, right: str) -> bool` functions to the hand-written
  `groundx.extract` package.
- Case-fold strings, remove whitespace, and map the approved classes `{0, o}`,
  `{1, i, l}`, and `{8, b}`. Preserve punctuation, length, and unmapped
  characters. Reject nonstring helper inputs; production callers retain their
  existing nonstring comparison behavior.
- Route every string component of repeated-record identity keys and relationship
  comparisons through those functions.
- Retire `identity_match.exact_attrs` as a runtime matching switch. Continue
  accepting existing metadata so old workflows remain readable.
- Keep comparison values transient. Do not rewrite extracted values, conflicts,
  provenance, X-Ray, diagnostics, or final output.
- Add new regression coverage without changing an existing test, fixture,
  expected output, or score. Any required existing-test change stops for human
  review and approval.
- **BREAKING**: repeated-record and relationship string equality becomes
  universal, so previously distinct case, whitespace, or approved OCR variants
  may merge or select the same parent.

## Capabilities

### New Capabilities

- `identifier-comparison`: Defines the shared comparison functions, restricted
  string transformation, exact-mode retirement, and raw-value preservation.

### Modified Capabilities

- `custom-output-readback`: Uses the shared comparison for repeated-record
  identity and relationship parent selection.

## Impact

- `src/groundx/extract/comparison.py`: new hand-written comparison owner.
- `src/groundx/extract/__init__.py`: exports both functions.
- `src/groundx/extract/custom_outputs.py`: removes duplicate string transforms
  from identity indexes, partitions, dedupe, thresholds, and parent selection.
- `tests/extract/`: adds function and production-entrypoint regressions.
- `internal-arcadia-agents`: consumes the released functions under its separate
  `adopt-confusable-identifier-matcher` change and updates its SDK pin.
- `eyelevel-fern-config`: a separate docs-only
  `document-universal-identifier-matching` change updates the public workflow
  contract before the SDK release.
- No dependency, Fern API schema, generated SDK shape, API, workflow YAML,
  Cashbot, Harness, database, or stored-data change.
- All touched source, tests, and OpenSpec paths are protected by `.fernignore`.
- Open design questions: none.

Rollback restores the prior GroundX Python release. No data repair is required
because comparison values are never persisted.
