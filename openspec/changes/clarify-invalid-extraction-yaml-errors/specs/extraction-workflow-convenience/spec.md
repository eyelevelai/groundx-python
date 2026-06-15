## MODIFIED Requirements

### Requirement: Python SDK exposes extraction workflow create/update helpers
The Python SDK SHALL expose hand-written convenience helpers that create and
update extraction workflows from `ExtractionDefinition` or authored extraction
YAML without requiring callers to manually copy persisted workflow metadata into
generated workflow client kwargs.

#### Scenario: Workflow create YAML shortcut preserves invalid YAML context
- **GIVEN** a local extraction YAML file with unsupported top-level metadata or
  another structural authoring error
- **WHEN** a caller invokes `GroundX.create_extraction_workflow(path=..., name=...)`
- **THEN** the SDK fails before calling the workflow API
- **AND** the error includes the YAML path or source context
- **AND** the error preserves the actionable loader message naming the offending
  key or malformed path

#### Scenario: Workflow create YAML shortcut accepts supported policy metadata
- **GIVEN** a local extraction YAML file with top-level
  `extraction_policy_version: v1`
- **WHEN** a caller invokes `GroundX.create_extraction_workflow(path=..., name=...)`
- **THEN** the SDK loads the YAML without caller-specific metadata registration
- **AND** the workflow API payload preserves the policy marker in `extract`

#### Scenario: Workflow update YAML shortcut preserves invalid YAML context
- **GIVEN** an existing workflow ID and a local extraction YAML file with
  unsupported top-level metadata or another structural authoring error
- **WHEN** a caller invokes
  `GroundX.update_extraction_workflow(id, path=..., name=...)`
- **THEN** the SDK fails before calling the workflow API
- **AND** the error includes the YAML path or source context
- **AND** the error preserves the actionable loader message naming the offending
  key or malformed path

#### Scenario: Workflow update YAML shortcut accepts supported policy metadata
- **GIVEN** an existing workflow ID and a local extraction YAML file with
  top-level `extraction_policy_version: v1`
- **WHEN** a caller invokes
  `GroundX.update_extraction_workflow(id, path=..., name=...)`
- **THEN** the SDK loads the YAML without caller-specific metadata registration
- **AND** the workflow API payload preserves the policy marker in `extract`

#### Scenario: Async workflow create YAML shortcut preserves invalid YAML context
- **GIVEN** a local extraction YAML file with unsupported top-level metadata or
  another structural authoring error
- **WHEN** a caller invokes
  `AsyncGroundX.create_extraction_workflow(path=..., name=...)`
- **THEN** the SDK fails before calling the workflow API
- **AND** the error includes the YAML path or source context
- **AND** the error preserves the actionable loader message naming the offending
  key or malformed path

#### Scenario: Async workflow create YAML shortcut accepts supported policy metadata
- **GIVEN** a local extraction YAML file with top-level
  `extraction_policy_version: v1`
- **WHEN** a caller invokes
  `AsyncGroundX.create_extraction_workflow(path=..., name=...)`
- **THEN** the SDK loads the YAML without caller-specific metadata registration
- **AND** the workflow API payload preserves the policy marker in `extract`

#### Scenario: Async workflow update YAML shortcut preserves invalid YAML context
- **GIVEN** an existing workflow ID and a local extraction YAML file with
  unsupported top-level metadata or another structural authoring error
- **WHEN** a caller invokes
  `AsyncGroundX.update_extraction_workflow(id, path=..., name=...)`
- **THEN** the SDK fails before calling the workflow API
- **AND** the error includes the YAML path or source context
- **AND** the error preserves the actionable loader message naming the offending
  key or malformed path

#### Scenario: Async workflow update YAML shortcut accepts supported policy metadata
- **GIVEN** an existing workflow ID and a local extraction YAML file with
  top-level `extraction_policy_version: v1`
- **WHEN** a caller invokes
  `AsyncGroundX.update_extraction_workflow(id, path=..., name=...)`
- **THEN** the SDK loads the YAML without caller-specific metadata registration
- **AND** the workflow API payload preserves the policy marker in `extract`
