## MODIFIED Requirements

### Requirement: Prepared extraction YAML exposes a persisted workflow extract payload
The SDK SHALL expose an explicit JSON-serializable mapping that preserves the authored
extraction YAML contract for storage in GroundX workflow `extract`.
`PreparedExtractionYaml` now also carries `custom_template`, `custom_steps`,
`output_routes`, and `leaf_fields` so that the full custom-step authoring surface
survives the `_groundx_persisted_extract` round-trip alongside all previously-existing
fields.

#### Scenario: Authored metadata survives JSON round trip
- **WHEN** YAML contains top-level metadata, final-group metadata, and
  workflow-only pseudo groups
- **THEN** `prepare_extraction_yaml(...)` exposes a persisted workflow extract mapping
- **AND** that mapping can be JSON serialized and deserialized without losing the
  authored metadata
- **AND** preparing the deserialized mapping recovers the same final groups, workflow
  groups, route metadata, top-level metadata, final-group metadata, and
  workflow-group metadata

#### Scenario: Custom-step authoring metadata survives JSON round trip
- **WHEN** YAML contains `_template`, `_custom_steps`, `_output_routes`, and
  `_leaf_fields` keys alongside ordinary group definitions
- **THEN** `prepare_extraction_yaml(...)` returns a `PreparedExtractionYaml` whose
  `custom_template`, `custom_steps`, `output_routes`, and `leaf_fields` fields are
  populated with the authored values
- **AND** the `persisted_workflow_extract` mapping includes those top-level keys
- **AND** `prepare_extraction_yaml` on the serialized-then-deserialized mapping
  recovers the same `custom_steps` entries (name, level, kind, optional config)

#### Scenario: Execution groups remain execution-only
- **WHEN** callers use `PromptManager.workflow_extract_dict()`
- **THEN** the returned mapping contains execution workflow groups only
- **AND** top-level metadata, final-group metadata, and pseudo group authoring
  sections are not exposed as workflow groups
- **AND** `_template`, `_custom_steps`, `_output_routes`, and `_leaf_fields` are not
  exposed as workflow groups

#### Scenario: Persisted payload is safe for workflow create and update
- **WHEN** the persisted workflow extract mapping is assigned to GroundX workflow
  create or update `extract`
- **THEN** the payload remains a JSON object accepted by the SDK workflow client
- **AND** workflow steps can still resolve the execution groups they reference
- **AND** the payload can still be prepared later as the authored extraction contract
  (including custom-step fields when present)

### Requirement: Prepared extraction YAML accepts persisted workflow extract mappings
The SDK SHALL support preparing extraction definitions from either raw YAML text or a
workflow API `extract` mapping produced by the persisted workflow extract surface.
This requirement now covers mappings that contain `_template`, `_custom_steps`,
`_output_routes`, and `_leaf_fields` within the embedded `_groundx_persisted_extract`
blob.

#### Scenario: Mapping input does not mutate caller data
- **WHEN** `prepare_extraction_yaml(...)` receives a mapping from workflow JSON `extract`
- **THEN** it prepares the extraction definition successfully
- **AND** it does not mutate the caller-owned mapping

#### Scenario: Custom steps recovered from workflow extract mapping
- **WHEN** `prepare_extraction_yaml(...)` receives a mapping that contains a
  `_groundx_persisted_extract` blob with `_custom_steps`
- **THEN** the returned `PreparedExtractionYaml` has `custom_steps` populated with the
  authored step entries
- **AND** step-level validation (name regex, level/kind enum) is re-run on the
  recovered steps

#### Scenario: Legacy YAML remains supported
- **WHEN** YAML does not include policy metadata, pseudo groups, `_template`,
  `_custom_steps`, `_output_routes`, or `_leaf_fields`
- **THEN** existing final group loading and execution workflow group behavior remain
  unchanged
- **AND** callers do not need to add `extraction_policy_version` or any custom-step key

#### Scenario: PromptManager falls back to deployed workflow extract
- **WHEN** `PromptManager` cannot fetch YAML from its configured prompt source
- **AND** it has a GroundX client and workflow ID
- **THEN** it fetches the workflow details through
  `gx_client.workflows.get(id=workflow_id)`
- **AND** it prepares the returned workflow `extract` mapping through the same SDK
  metadata and route-map path (including recovery of custom-step fields when present)
- **AND** the local cache source remains a final fallback for legacy callers
