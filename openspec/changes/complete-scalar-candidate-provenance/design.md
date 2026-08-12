# Design: Complete scalar candidate provenance

## Goal

Allow singular routed fields to observe every section and document occurrence
while preserving the existing repeated-record deduplication contract.

## Current loss point

`_route_containers()` discards evidence in two places before
`_custom_route_values()` or `_set_pointer()` can inspect it:

- Section routes use `custom_output_section_identity()` and one `section_seen`
  set. Later chunks with the same explicit section ID are discarded.
- Document routes deduplicate root and chunk copies by payload identity. The
  surviving container has no page numbers, even when the copied observations
  came from numbered chunks.

The narrow correction belongs at this route boundary. Changing only
`_set_pointer()` cannot recover observations already discarded.

## Implementation

Add one shared private repeated-route predicate used by
`_route_containers()`, `_custom_route_values()`, and final placement. A route is
repeated when its step kind is `keys` or `summary`, or its parsed `final_path`
contains `*`. Repeatedness must not be inferred from `final_path` alone.

Pass that predicate's result into `_set_pointer()`. Existing wildcard routes
keep their current placement. For a repeated `keys` or `summary` route without
`*`, `_set_pointer()` treats the first path segment as the top-level list and
the remaining segments as fields in the repeated record. This is the narrow
implementation of the existing `custom-output-readback` requirement. It does
not alter singular routes or invent placement from a group name.

For `level: section` routes:

1. Use the shared repeated-route predicate.
2. If the route is repeated, preserve current section-ID deduplication.
3. If the path is singular, emit one `_RouteContainer` per chunk. Use the chunk
   identity for traversal bookkeeping and retain that chunk's page numbers.
4. Let scalar candidate collection apply its approved value identity rules.
   Equal values merge pages. Distinct values remain candidates in traversal
   order.

For `level: document` routes:

1. If the route is repeated, preserve current payload-identity deduplication.
2. If the route is singular, emit the document-root observation when present
   and every chunk observation with its page numbers.
3. Let scalar candidate collection merge equal values and their pages. Do not
   invent a page for a root-only observation.

No second candidate deduplicator is added. No value meaning, confidence,
default text, or page presence participates in this routing decision.

## Compatibility

- Chunk-level routes are unchanged.
- Repeated section records still deduplicate by section identity.
- Repeated document records still deduplicate by payload identity.
- Direct repeated groups owned by `keys` or `summary` remain repeated even when
  their final paths contain no `*`.
- Singular section output keeps the first observed candidate in provisional
  `final_output`, as defined by the companion scalar-candidate plan.
- `source_provenance` may contain multiple observation records. Candidate page
  lists remain unique and first-seen ordered.
- The public `CustomOutputReassemblyResult` and
  `CustomOutputScalarCandidateSet` shapes do not change.

## Verification

The focused regression uses three chunks with the same explicit section ID:

- page 12 returns `A`;
- page 14 returns `A`;
- page 16 returns `B`.

The selected candidate must be `A` with pages `(12, 14)`. The alternative must
be `B` with page `(16,)`.

A separate repeated-record regression uses a direct top-level `keys` route with
no `*`, copies it across chunks with the same section ID, and proves the
existing single repeated record remains unchanged.

A document-level regression uses root and chunk copies where pages 12 and 14
return `A` and page 16 returns `B`. It proves `A` retains pages `(12, 14)`, `B`
retains page `(16,)`, and no page is invented for a root-only observation. A
repeated document regression proves producer-copy deduplication remains
unchanged for both wildcard and direct `keys` routes.

The complete extraction suite then protects chunk, section, document,
relationship, and repeated-route behavior.

## Release dependency

This change completes Tasks 1 and 2 before
`delegate-scalar-candidate-resolution-to-agents` builds the one unpublished
source candidate from the combined commit. The candidate keeps the repository's
generated package version and records its source commit and SHA-256. Internal
Arcadia and Studio Harness test only that candidate on Python 3.11 before the
human release owner publishes requested version 3.9.7. After publication, both
consumers verify the released package contains the same handwritten source
change and rerun their gates from a clean install. The differently versioned
wheels are not required to be byte-identical. This repository does not publish
the package.
