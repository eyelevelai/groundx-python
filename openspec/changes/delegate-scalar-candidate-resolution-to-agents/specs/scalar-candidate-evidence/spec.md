## ADDED Requirements

### Requirement: Singular scalar observations are preserved without semantic ranking

The SDK SHALL keep the first observed singular routed scalar value as the
provisional selected value and SHALL retain every later unique value in
observation order. It SHALL NOT select, replace, filter, or order candidates
using value meaning, default-like text, source-page presence, or confidence.

#### Scenario: Later value looks more specific

- **GIVEN** the first candidate is `N/A`
- **AND** a later candidate is `100% immediate`
- **WHEN** the SDK reassembles the routed scalar field
- **THEN** `N/A` remains the provisional selected value
- **AND** `100% immediate` is retained as an alternative
- **AND** both values are available to the downstream reconciliation agent.

#### Scenario: Later value has source pages or higher confidence

- **GIVEN** a first candidate has no pages or lower confidence
- **AND** a later distinct candidate has pages or higher confidence
- **WHEN** the SDK reassembles the routed scalar field
- **THEN** the first candidate remains selected
- **AND** the later candidate remains an alternative
- **AND** neither page presence nor confidence changes their order.

### Requirement: Candidate deduplication uses only value identity

The SDK SHALL deduplicate string candidates after trimming leading and trailing
whitespace and comparing case-insensitively. It SHALL preserve internal string
whitespace. Other JSON values SHALL compare exactly and type-sensitively. A
known extracted-field envelope SHALL compare by its inner `value` while
retaining the first envelope and its metadata.

#### Scenario: String differs only by case and outer whitespace

- **GIVEN** candidates `" January 1 "` and `"january 1"`
- **WHEN** the SDK reassembles the field
- **THEN** it retains one candidate with the first casing and trimmed outer
  whitespace.

#### Scenario: String has different internal whitespace

- **GIVEN** candidates `"January 1"` and `"January  1"`
- **WHEN** the SDK reassembles the field
- **THEN** it retains both candidates.

#### Scenario: JSON values have different types

- **GIVEN** candidates `true`, `1`, and `1.0`
- **WHEN** the SDK reassembles the field
- **THEN** it retains all three as distinct candidates.

#### Scenario: Envelopes have equal values and different confidence

- **GIVEN** two extracted-field envelopes have the same inner value after
  string comparison
- **AND** the envelopes have different confidence values
- **WHEN** the SDK reassembles the field
- **THEN** it retains the first envelope
- **AND** confidence does not create, remove, reorder, or replace a candidate.

### Requirement: Explicit empty values remain candidates

For a singular routed scalar field, the SDK SHALL distinguish a missing output
key from a key present with null, empty string, or empty list. It SHALL preserve
each present value as a candidate.

#### Scenario: Output key is missing

- **WHEN** a routed output container has no key for the field
- **THEN** the SDK creates no candidate from that container.

#### Scenario: Output key contains an explicit empty value

- **GIVEN** separate observations contain null, empty string, and empty list
- **WHEN** the SDK reassembles the routed scalar field
- **THEN** each present value is retained according to candidate identity rules
- **AND** none is discarded as absence.

### Requirement: Duplicate observations retain all source pages

The SDK SHALL merge every unique source page associated with duplicate
candidate observations. It SHALL preserve first-seen page order and SHALL NOT
discard pages because the candidate value is duplicated.

#### Scenario: Duplicate value appears on multiple pages

- **GIVEN** equal candidate observations occur on pages 12, 14, and 12
- **WHEN** the SDK reassembles the field
- **THEN** one candidate remains
- **AND** its page numbers are `[12, 14]`.

### Requirement: Existing public result shape exposes provisional candidates

The SDK SHALL preserve the public `CustomOutputScalarCandidateSet` shape.
`selected` SHALL contain the first observed candidate, `alternatives` SHALL
contain every later unique candidate, and `final_output` SHALL contain the
selected candidate before downstream reconciliation.

#### Scenario: Consumer reads a multi-candidate result

- **GIVEN** a routed field has three unique candidates
- **WHEN** the consumer reads the reassembly result
- **THEN** the first candidate appears in `selected` and `final_output`
- **AND** the second and third appear in `alternatives` in observation order
- **AND** no candidate is described or represented as SDK-resolved.

### Requirement: Reconciliation receives complete candidate provenance

The Internal Arcadia consumer SHALL reconcile every statement field with more
than one unique candidate. Its prompt SHALL include every candidate value,
every known source page, and the subset of pages whose images are attached to
the request.

#### Scenario: Candidate has more pages than are attached

- **GIVEN** a candidate has source pages 32 and 43
- **AND** only page 32 is attached under the image limit
- **WHEN** Arcadia renders the reconcile prompt
- **THEN** the candidate object contains `source_pages: [32, 43]`
- **AND** it contains `provided_pages: [32]`
- **AND** the prompt does not imply that page 43 is visible to the agent.

#### Scenario: Values include default-like text

- **GIVEN** the candidate set contains `N/A` and another value
- **WHEN** Arcadia prepares reconciliation
- **THEN** it runs the reconciliation agent
- **AND** it does not suppress either value based on meaning or confidence.

### Requirement: Image selection covers candidates fairly within 30 images

The Internal Arcadia consumer SHALL attach at least one available page image per
candidate before adding additional pages. It SHALL then add remaining candidate
pages round-robin in candidate order, deduplicate page images, and stop at the
configured 30-image limit.

#### Scenario: Total source pages exceed the image limit

- **GIVEN** a field has fewer than or equal to 30 candidates
- **AND** their combined source pages exceed 30 images
- **WHEN** Arcadia selects reconcile images
- **THEN** every candidate with an available page receives at least one image
- **AND** remaining slots are distributed round-robin
- **AND** every omitted page remains listed in `source_pages`.

#### Scenario: Candidate coverage itself exceeds the image limit

- **GIVEN** one field has more than 30 candidates that each require a distinct
  available page
- **WHEN** Arcadia prepares reconciliation
- **THEN** it raises a clear image-evidence error before the model call
- **AND** it does not hide a candidate or run a partial reconciliation.

### Requirement: Agent decisions update output without erasing evidence

After a valid reconciliation response, Internal Arcadia SHALL make the returned
value current, clear the pending conflict marker, and preserve candidate
history. QA SHALL preserve the same history.

#### Scenario: Reconcile selects an existing candidate

- **GIVEN** the provisional value is `A` and another candidate is `B`
- **AND** the reconciliation agent returns `B`
- **WHEN** Arcadia applies the response
- **THEN** `B` becomes the current routed value
- **AND** `A` and `B` remain in candidate history with their source pages
- **AND** the pending conflict marker is cleared.

#### Scenario: Reconcile returns a novel value

- **GIVEN** candidate history contains `A` and `B`
- **AND** the reconciliation agent returns `C`
- **WHEN** Arcadia applies the response
- **THEN** `C` becomes the current routed value
- **AND** `C` is appended to candidate history with reconcile-agent origin
- **AND** Arcadia invents no source page for `C`.

#### Scenario: QA changes the reconciled value

- **GIVEN** reconciliation has selected a current value and preserved candidate
  history
- **WHEN** QA returns a different valid value
- **THEN** the QA value becomes current
- **AND** the previous history remains
- **AND** a novel QA value is appended without invented source pages.

### Requirement: Confidence is metadata only

GroundX Python and Internal Arcadia SHALL NOT use confidence to select, replace,
filter, order, deduplicate, reconcile, accept, or reject a candidate, or to
select its evidence images.

#### Scenario: Candidate confidence values disagree

- **GIVEN** otherwise distinct candidates have different confidence values
- **WHEN** the SDK and Arcadia process them
- **THEN** observation order and agent decisions alone determine the
  provisional and reconciled values
- **AND** confidence may be preserved as metadata
- **AND** it causes no code branch affecting value or evidence selection.

### Requirement: Protected extraction paths retain behavior outside candidate selection

The coordinated SDK and Internal Arcadia change SHALL preserve workflow routes,
relationships, agent response parsing, type coercion, retry ownership, and final
customer JSON shape across the current reproduction, Arcadia legacy, Arcadia
v1, generic v1, and ADP protected cases.

#### Scenario: Field has one candidate

- **GIVEN** a protected extraction field has one unique candidate
- **WHEN** the coordinated pipeline runs
- **THEN** candidate conflict alone does not invoke reconciliation
- **AND** existing routing and output behavior remains unchanged.

#### Scenario: Field has competing candidates

- **GIVEN** a protected extraction field has more than one unique candidate
- **WHEN** the coordinated pipeline runs
- **THEN** reconciliation receives all candidates and available provenance
- **AND** the reconciled current value reaches the existing final output path
- **AND** candidate history remains diagnostic runtime state rather than a new
  customer output field.
