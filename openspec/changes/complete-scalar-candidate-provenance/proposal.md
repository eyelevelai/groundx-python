# Proposal: Complete scalar candidate provenance

## Why

`delegate-scalar-candidate-resolution-to-agents` requires the SDK to preserve
every scalar observation and every source page. The current section-container
loader deduplicates chunks by explicit section ID before scalar candidates are
collected. When multiple chunks share a section ID, only the first chunk's value
and pages reach candidate collection.

This is not the cause of the current ADP run's failures. Its 251 chunks across
68 pages have no top-level section identifier. It is still a supported X-Ray
shape and violates the candidate transport contract for other documents.

## What changes

- Singular section routes process every chunk observation, even when chunks
  share an explicit section ID.
- Existing scalar candidate identity removes duplicate values and merges their
  unique page numbers.
- Distinct values from chunks sharing a section ID remain distinct candidates.
- Repeated section routes keep their current section-record deduplication.
- Relationship matching, repeated-record identity, route placement, and public
  result types do not change.

## Relationship to active plans

- This change is a companion to
  `delegate-scalar-candidate-resolution-to-agents`. It does not replace, edit,
  close, or archive that change.
- It does not replace or close Internal Arcadia's
  `complete-extraction-boundary-regression-coverage` change or Studio Harness's
  `add-extraction-certification-harness` change.
- Implementation starts from the candidate collection behavior defined by
  `delegate-scalar-candidate-resolution-to-agents`. Both changes ship in the
  same requested GroundX Python 3.9.7 release.

## Capabilities

### New capabilities

- `scalar-candidate-provenance`: complete page provenance for singular scalar
  observations that share a section identity.

### Modified capabilities

- None.

## Impact

- Hand-written implementation:
  `src/groundx/extract/custom_outputs.py`.
- Hand-written tests:
  `tests/extract/test_custom_output_reassembly.py`.
- Public dataclasses and imports remain unchanged.
- Singular section routes may expose candidates and page numbers that were
  previously lost. This is the intended correction.
- Repeated section output remains byte-for-byte compatible after reassembly.
- The implementation stays under paths protected by `.fernignore`.
- No workflow, API, database, customer JSON, or generated Fern change.
- Open design questions: none.
