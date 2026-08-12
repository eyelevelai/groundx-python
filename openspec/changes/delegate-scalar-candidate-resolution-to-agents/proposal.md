# Proposal: Delegate scalar candidate resolution to agents

## Why

GroundX Python currently ranks competing scalar extraction values in code. It
prefers values that look more specific, have source pages, or have higher
confidence. A later higher-ranked value replaces the selected value and clears
lower-ranked alternatives. This hides evidence before the reconciliation agent
can review it.

Internal Arcadia already has a reconciliation agent whose main job is to select
the correct value from competing values and source pages. It now consumes the
SDK candidate sidecar, but the SDK can omit candidates and Arcadia sends only a
plain value array with representative images. The agent does not receive the
complete value-to-page mapping.

## What changes

- GroundX Python keeps the first observed scalar value as a provisional value.
- It retains every later unique value in observation order. Code does not rank,
  replace, or discard values based on meaning, source-page presence, or
  confidence.
- String comparison trims leading and trailing whitespace and ignores case.
  No other normalization is used to decide whether values are duplicates.
- Explicit null, empty-string, and empty-list outputs remain candidates. A
  missing field remains no candidate.
- Explicit null remains diagnostic evidence but does not satisfy a required
  route. A sole nullable null is omitted from customer output by the consumer
  from the authored field contract, without an agent value decision.
- Duplicate values merge all source page numbers into the retained candidate.
- The existing public `selected` and `alternatives` shape remains unchanged.
  `selected` means first observed, not best or final.
- SDK `final_output` keeps the first observed value for compatibility. For a
  field with multiple candidates, it is provisional until the consumer runs
  reconciliation.
- Internal Arcadia reconciles every statement field with more than one unique
  candidate. It sends every candidate, every source-page number, and the pages
  actually attached to the model request.
- The reconciliation response becomes the current routed value. Candidate
  evidence remains intact. A novel agent value is appended as agent-produced
  evidence without invented source pages.
- QA may verify or change the current value, but it cannot erase candidate
  history. A novel QA value is recorded the same way.
- Confidence remains transport metadata. Neither repository may use it to
  select, order, filter, or branch on candidate values.
- Reconciliation remains single-pass. Arcadia attaches at least one available
  page for each candidate, then fills remaining slots fairly up to the existing
  30-image limit. Full source-page lists remain in the prompt. A field with more
  than 30 candidates that each require a distinct available image fails clearly
  instead of hiding a candidate.

## Capabilities

### New capabilities

- `scalar-candidate-evidence`: deterministic collection, transport, agent
  review, and preservation of competing scalar extraction values.

### Modified capabilities

- None. The existing public SDK result shape is preserved.

## Impact

- SDK implementation:
  `src/groundx/extract/custom_outputs.py` and its hand-written tests.
- SDK public behavior: `CustomOutputScalarCandidateSet.selected` becomes the
  first observed candidate. `alternatives` contains every later unique
  candidate. The dataclass shape and imports do not change.
- Consumer implementation: Internal Arcadia statement load, reconcile, QA,
  candidate-evidence serialization, image selection, prompt rendering, and
  tests are owned only by its `complete-scalar-reconcile-disposition` change.
  This SDK change owns the producer contract and coordinated acceptance gates,
  not Arcadia code.
- Downstream consumers: `internal-arcadia-agents` must pin the released SDK
  before deploying this behavior. Other consumers receive the same public
  types but may observe different `selected`, `alternatives`, and provisional
  `final_output` values when candidates compete.
- Generated Fern code is not affected. All SDK changes stay under paths
  protected by `.fernignore`, including `src/groundx/extract/`,
  `tests/extract/`, and `openspec/`.
- No workflow schema, stored workflow, customer output schema, database, or
  data migration changes.
- Rollback is the prior SDK pin and prior Internal Arcadia container image.
- Open design questions: none.

## Release order

1. Implement and test Tasks 0 through 2 in this change on Python 3.11.
2. Implement and test Tasks 1 and 2 in the companion
   `complete-scalar-candidate-provenance` change on top of the same branch.
3. Only after both SDK changes are complete, build one unpublished
   source-candidate wheel from the combined commit using the repository's
   generated package version. Record that commit, filename, and SHA-256.
4. Install only that source candidate in isolated Internal Arcadia and Studio
   Harness checkouts. Internal Arcadia implements its consumer contract only
   through `complete-scalar-reconcile-disposition`.
5. Merge both SDK changes and give the merged handwritten source commit and
   validation evidence to the human release owner for requested version 3.9.7.
6. After 3.9.7 is published, verify that it contains the tested handwritten
   source change. Clean-install the published artifact and rerun both consumer
   gates. Do not require wheel-byte identity across different package versions.
7. Pin the published SDK in both Internal Arcadia dependency writers, rerun
   protected tests, build and inspect the extract container, then merge and
   deploy Internal Arcadia.
