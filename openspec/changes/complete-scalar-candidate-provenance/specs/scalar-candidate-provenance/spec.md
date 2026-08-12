## ADDED Requirements

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

The SDK SHALL keep existing section-identity deduplication for routed paths that
contain a repeated-record `*` segment.

#### Scenario: Copied repeated output shares a section ID

- **GIVEN** multiple chunks share one explicit section ID
- **AND** each chunk carries the same repeated section records
- **WHEN** the SDK reassembles a routed repeated path
- **THEN** it emits the existing single set of repeated records
- **AND** singular candidate preservation does not duplicate those records.

### Requirement: Candidate provenance remains transport-only

The SDK SHALL use only the candidate identity rules owned by
`delegate-scalar-candidate-resolution-to-agents` to merge singular values and
pages after section routing.

#### Scenario: Section observations differ in confidence or page presence

- **GIVEN** singular section observations have different confidence values or
  different source-page availability
- **WHEN** the SDK collects candidates
- **THEN** those metadata differences do not select, discard, replace, or order
  candidate values
- **AND** every observed source page remains attached to its value.
