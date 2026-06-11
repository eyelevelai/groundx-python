## ADDED Requirements

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
