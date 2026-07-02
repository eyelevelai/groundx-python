## ADDED Requirements

### Requirement: Extraction YAML shape classification is explicit

The SDK SHALL classify extraction definitions into accepted authored,
workflow-extract, and invalid mixed shapes before preparing them for workflow
create or update.

#### Scenario: Pure legacy authored YAML remains supported

- **GIVEN** YAML contains only top-level extraction groups with field
  definitions
- **AND** it does not contain v1 workflow metadata, pseudo groups, route
  metadata, policy metadata, or `_groundx_persisted_extract`
- **WHEN** the SDK prepares the YAML
- **THEN** the definition is classified as pure legacy authored YAML
- **AND** existing legacy preparation behavior remains supported.

#### Scenario: V1 authored YAML requires explicit marker

- **GIVEN** YAML contains v1 workflow metadata, pseudo groups, route metadata,
  policy metadata, or workflow-only field routing keys
- **WHEN** the SDK prepares the YAML
- **THEN** preparation succeeds only when top-level
  `extraction_policy_version: v1` is present
- **AND** preparation fails clearly when that marker is absent.

#### Scenario: Persisted workflow extract is not guessed from simple groups

- **GIVEN** a mapping contains simple extraction group keys that could be either
  authored YAML or an execution-only workflow `extract`
- **WHEN** the caller does not pass `mapping_kind="workflow_extract"`
- **THEN** the SDK treats the mapping as authored YAML-shaped input
- **AND** it does not guess workflow-extract semantics from the group names
  alone.

#### Scenario: Mixed metadata shape fails clearly

- **GIVEN** an extraction mapping contains partial persisted metadata, v1 field
  routing keys in reserved metadata positions without the v1 marker, or v1
  metadata keys mixed into legacy groups
- **WHEN** the SDK prepares the mapping
- **THEN** preparation fails with an error that identifies the invalid shape
- **AND** the error says pure legacy and explicitly marked v1 are the supported
  authored YAML shapes.

#### Scenario: Legacy customer field names are not treated as v1 metadata

- **GIVEN** pure legacy YAML contains a customer field name, prompt text, or
  identifier whose string matches a reserved v1 metadata word
- **WHEN** the SDK prepares the YAML
- **THEN** preparation does not reject the YAML solely because of that string
- **AND** reserved v1 metadata detection is based on YAML position and structure,
  not substring matching.

### Requirement: Persisted workflow extracts preserve v1 metadata

The SDK SHALL preserve v1 persisted workflow extract metadata across JSON round
trips and workflow helper loading.

#### Scenario: V1 persisted extract reloads as v1

- **GIVEN** a persisted workflow extract produced from v1 authored YAML
- **WHEN** the mapping is serialized to JSON, deserialized, and loaded again
- **THEN** the SDK recovers the v1 top-level metadata, route metadata, workflow
  groups, and final groups
- **AND** the loaded definition is not reclassified as pure legacy.

#### Scenario: Execution-only workflow extract stays opaque

- **GIVEN** a workflow `extract` mapping lacks authored persisted metadata
- **WHEN** the caller loads it with `mapping_kind="workflow_extract"`
- **THEN** the SDK preserves the mapping exactly
- **AND** it does not fabricate authored metadata or v1 route metadata.
