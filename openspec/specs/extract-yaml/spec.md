# extract-yaml Specification

## Purpose
Define how the hand-written extraction YAML loader prepares final extraction
groups, workflow execution groups, routing metadata, and persisted workflow
extract payloads.
## Requirements
### Requirement: Prepared extraction YAML exposes a persisted workflow extract payload
The SDK SHALL expose an explicit JSON-serializable mapping that preserves the
authored extraction YAML contract for storage in GroundX workflow `extract`.

#### Scenario: Authored metadata survives JSON round trip
- **WHEN** YAML contains top-level metadata, final-group metadata, and
  workflow-only pseudo groups
- **THEN** `prepare_extraction_yaml(...)` exposes a persisted workflow extract
  mapping
- **AND** that mapping can be JSON serialized and deserialized without losing
  the authored metadata
- **AND** preparing the deserialized mapping recovers the same final groups,
  workflow groups, route metadata, top-level metadata, final-group metadata,
  and workflow-group metadata

#### Scenario: Execution groups remain execution-only
- **WHEN** callers use `PromptManager.workflow_extract_dict()`
- **THEN** the returned mapping contains execution workflow groups only
- **AND** top-level metadata, final-group metadata, and pseudo group authoring
  sections are not exposed as workflow groups

#### Scenario: Persisted payload is safe for workflow create and update
- **WHEN** the persisted workflow extract mapping is assigned to GroundX
  workflow create or update `extract`
- **THEN** the payload remains a JSON object accepted by the SDK workflow client
- **AND** workflow steps can still resolve the execution groups they reference
- **AND** the payload can still be prepared later as the authored extraction
  contract

### Requirement: Prepared extraction YAML accepts persisted workflow extract mappings
The SDK SHALL support preparing extraction definitions from either raw YAML text
or a workflow API `extract` mapping produced by the persisted workflow extract
surface.

#### Scenario: Mapping input does not mutate caller data
- **WHEN** `prepare_extraction_yaml(...)` receives a mapping from workflow JSON
  `extract`
- **THEN** it prepares the extraction definition successfully
- **AND** it does not mutate the caller-owned mapping

#### Scenario: Legacy YAML remains supported
- **WHEN** YAML does not include policy metadata or pseudo groups
- **THEN** existing final group loading and execution workflow group behavior
  remain unchanged
- **AND** callers do not need to add `extraction_policy_version`

#### Scenario: PromptManager falls back to deployed workflow extract
- **WHEN** `PromptManager` cannot fetch YAML from its configured prompt source
- **AND** it has a GroundX client and workflow ID
- **THEN** it fetches the workflow details through
  `gx_client.workflows.get(id=workflow_id)`
- **AND** it prepares the returned workflow `extract` mapping through the same
  SDK metadata and route-map path
- **AND** the local cache source remains a final fallback for legacy callers

#### Scenario: Unsupported top-level scalar metadata fails clearly
- **WHEN** raw authored YAML contains a top-level scalar key that is not a
  reserved SDK key, not supported SDK metadata, and was not registered through
  `top_level_metadata_keys`
- **THEN** `prepare_extraction_yaml(...)` raises a `ValueError` naming the
  offending key
- **AND** the error explains that generic SDK top-level keys must be extraction
  groups, reserved SDK keys, or supported SDK metadata keys
- **AND** the error tells advanced callers to register metadata keys through
  `top_level_metadata_keys` or convert the YAML to supported workflow metadata

#### Scenario: Supported policy version metadata is preserved
- **WHEN** raw authored YAML contains top-level
  `extraction_policy_version: v1`
- **THEN** `prepare_extraction_yaml(...)` succeeds without caller-specific
  metadata registration
- **AND** the marker is exposed in `PreparedExtractionYaml.top_level_metadata`
- **AND** the marker is preserved in the persisted workflow extract

#### Scenario: Explicit metadata registration still works
- **WHEN** the same authored YAML is prepared with the scalar key included in
  `top_level_metadata_keys`
- **THEN** preparation succeeds
- **AND** the key is exposed as top-level metadata rather than as an extraction
  group

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
