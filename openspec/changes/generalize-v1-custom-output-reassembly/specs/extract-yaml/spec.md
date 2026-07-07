## ADDED Requirements

### Requirement: Extraction YAML preserves custom step output kind semantics

The SDK SHALL preserve the existing custom step kind values and their output
shape semantics in prepared definitions and persisted workflow extracts.

#### Scenario: Keys kind survives persisted extract round trip

- **GIVEN** v1 authored YAML declares a custom step with `kind: keys`
- **AND** a direct final group assigns itself to that step with `workflow_step`
- **WHEN** `prepare_extraction_yaml(...)` creates a persisted workflow extract
- **AND** the persisted extract is serialized, deserialized, and prepared again
- **THEN** the prepared definition still exposes that step as repeated-record
  output
- **AND** route metadata is still available for custom-output reassembly.

#### Scenario: Direct repeatedness is derivable without wildcard paths

- **GIVEN** v1 authored YAML declares a direct final group assigned to
  `kind: keys` or `kind: summary`
- **AND** the prepared route `final_path` has two segments such as
  `/line_items/description`
- **WHEN** the persisted workflow extract is used for readback
- **THEN** consumers can derive that the route is repeated from
  `workflow.custom_steps[].kind` and `workflow.output_routes`
- **AND** consumers do not need an authored `shape` field or final group name
  convention.

#### Scenario: Summary kind survives persisted extract round trip

- **GIVEN** v1 authored YAML declares a custom step with `kind: summary`
- **WHEN** `prepare_extraction_yaml(...)` creates a persisted workflow extract
- **AND** the persisted extract is serialized, deserialized, and prepared again
- **THEN** `summary` is still treated as repeated-record output
- **AND** route metadata is still available for custom-output reassembly.

#### Scenario: Instruct kind survives persisted extract round trip

- **GIVEN** v1 authored YAML declares a custom step with `kind: instruct`
- **WHEN** `prepare_extraction_yaml(...)` creates a persisted workflow extract
- **AND** the persisted extract is serialized, deserialized, and prepared again
- **THEN** `instruct` is still treated as singular-object output.

#### Scenario: Legacy YAML does not require custom workflow kinds

- **GIVEN** pure legacy extraction YAML has no v1 workflow metadata
- **WHEN** the SDK prepares the YAML
- **THEN** existing legacy preparation behavior is unchanged.

### Requirement: Extraction YAML preserves relationship metadata

The SDK SHALL preserve v1 `workflow.output_relationships` metadata through
preparation, persistence, reload, and schema hashing.

#### Scenario: Relationship metadata survives persisted extract round trip

- **GIVEN** v1 authored YAML declares `workflow.output_relationships`
- **WHEN** `prepare_extraction_yaml(...)` creates a persisted workflow extract
- **AND** the persisted extract is serialized, deserialized, and prepared again
- **THEN** the prepared definition still exposes the normalized relationship
  metadata
- **AND** the original source YAML is not required for relationship readback.

#### Scenario: Relationship metadata participates in schema hashing

- **GIVEN** two v1 authored YAML files differ only in
  `workflow.output_relationships`
- **WHEN** the SDK computes their schema hashes
- **THEN** the hashes are different.

#### Scenario: Existing final-group relationship metadata can become workflow metadata

- **GIVEN** v1 authored YAML has final-group relationship metadata with
  `match_attrs`
- **AND** the metadata also names an unambiguous parent group through an existing
  supported key such as `passthrough.from`
- **WHEN** `prepare_extraction_yaml(...)` creates a persisted workflow extract
- **THEN** canonical `workflow.output_relationships` is written into the
  persisted workflow metadata
- **AND** no primary output selection is implied.

#### Scenario: Ambiguous final-group match attrs do not create relationships

- **GIVEN** v1 authored YAML has final-group `match_attrs`
- **AND** no direct `workflow.output_relationships` entry or supported parent
  metadata exists
- **WHEN** `prepare_extraction_yaml(...)` creates a persisted workflow extract
- **THEN** no parent-child relationship is inferred from `match_attrs` alone.
