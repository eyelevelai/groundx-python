# scalar-candidate-provenance Specification

## Purpose
Define how the SDK preserves singular section and document observations without
changing repeated-route deduplication.

## Requirements
### Requirement: Singular section routes preserve every observation

The SDK SHALL pass every singular section-route observation to scalar candidate
collection even when multiple chunks share an explicit section identifier.

#### Scenario: Shared section ID contains duplicate and competing values

- **GIVEN** three section chunks share one explicit section ID
- **AND** pages 12 and 14 return scalar value `A`
- **AND** page 16 returns scalar value `B`
- **WHEN** the SDK reassembles a singular routed field
- **THEN** it retains `A` once with source pages 12 and 14
- **AND** it retains `B` as a distinct candidate with source page 16
- **AND** no chunk is discarded before candidate comparison.

### Requirement: Repeated section deduplication remains unchanged

The SDK SHALL keep existing section-identity deduplication for routes that are
repeated by `keys` or `summary` step kind or by a repeated-record `*` segment.

#### Scenario: Copied repeated output shares a section ID

- **GIVEN** multiple chunks share one explicit section ID
- **AND** each chunk carries the same repeated section records
- **WHEN** the SDK reassembles a routed repeated path
- **THEN** it emits the existing single set of repeated records
- **AND** singular candidate preservation does not duplicate those records.

#### Scenario: Direct repeated group has no wildcard

- **GIVEN** a `keys` or `summary` section step routes records through a direct
  top-level path such as `/line_items/description`
- **AND** copied chunks share one explicit section ID
- **WHEN** the SDK reassembles the route
- **THEN** it treats the route as repeated
- **AND** it emits one set of repeated records.

### Requirement: Singular document routes preserve every sourced observation

The SDK SHALL pass every singular document-route observation to scalar
candidate collection and preserve every available chunk page number.

#### Scenario: Document output is copied to root and chunks

- **GIVEN** a singular document output appears at the document root and on
  multiple numbered chunks
- **AND** pages 12 and 14 return scalar value `A`
- **AND** page 16 returns scalar value `B`
- **WHEN** the SDK reassembles the routed field
- **THEN** it retains `A` once with source pages 12 and 14
- **AND** it retains `B` as a distinct candidate with source page 16
- **AND** it does not invent a page for a root-only observation.

### Requirement: Repeated document deduplication remains unchanged

The SDK SHALL keep existing payload-identity deduplication for document routes
that are repeated by step kind or wildcard path.

#### Scenario: Copied repeated document output

- **GIVEN** repeated document output is copied to the document root and chunks
- **WHEN** the SDK reassembles a wildcard route or a direct top-level `keys`
  route
- **THEN** it emits one set of repeated records
- **AND** singular document provenance does not duplicate those records.

### Requirement: Candidate provenance remains transport-only

The SDK SHALL use only the candidate identity rules in
`custom-output-readback` to merge singular values and pages after section
routing.

#### Scenario: Candidate observations differ in confidence or page presence

- **GIVEN** singular section or document observations have different confidence values or
  different source-page availability at section or document level
- **WHEN** the SDK collects candidates
- **THEN** those metadata differences do not select, discard, replace, or order
  candidate values
- **AND** every observed source page remains attached to its value.
