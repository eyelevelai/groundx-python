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
