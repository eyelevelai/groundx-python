# Design: Complete scalar candidate provenance

## Goal

Allow singular routed fields to observe every section chunk while preserving
the existing repeated-record deduplication contract.

## Current loss point

`_route_containers()` uses `custom_output_section_identity()` and one
`section_seen` set for every section route. An explicit section ID becomes the
identity. Later chunks with that ID are discarded before `_custom_route_values()`
or `_set_pointer()` can inspect their values or page numbers.

The narrow correction belongs at this route boundary. Changing only
`_set_pointer()` cannot recover observations already discarded.

## Implementation

For `level: section` routes:

1. Parse `final_path` with the existing pointer helper.
2. If the path contains `*`, preserve the current section-ID deduplication.
3. If the path is singular, emit one `_RouteContainer` per chunk. Use the chunk
   identity for traversal bookkeeping and retain that chunk's page numbers.
4. Let scalar candidate collection apply its approved value identity rules.
   Equal values merge pages. Distinct values remain candidates in traversal
   order.

No second candidate deduplicator is added. No value meaning, confidence,
default text, or page presence participates in this routing decision.

## Compatibility

- Chunk-level and document-level routes are unchanged.
- Repeated section records still deduplicate by section identity.
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

A separate repeated-record regression uses the same section ID on multiple
chunks and proves the existing single repeated record remains unchanged.

The complete extraction suite then protects chunk, section, document,
relationship, and repeated-route behavior.

## Release dependency

This change joins the exact candidate wheel produced for
`delegate-scalar-candidate-resolution-to-agents`. Internal Arcadia and Studio
Harness test that wheel before the human release owner publishes requested
version 3.9.7. This repository does not publish the package.
