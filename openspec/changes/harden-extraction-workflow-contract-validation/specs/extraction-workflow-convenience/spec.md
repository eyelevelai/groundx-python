## ADDED Requirements

### Requirement: Extraction workflow create/update validates supported shapes

The SDK first-class extraction workflow helpers SHALL validate input definition
shape before calling the workflow API.

#### Scenario: Create accepts pure legacy

- **GIVEN** a caller creates an extraction workflow from pure legacy YAML
- **WHEN** `create_extraction_workflow(...)` validates the source
- **THEN** the helper accepts the definition
- **AND** it sends a legacy-compatible workflow `extract` payload.

#### Scenario: Create accepts explicit v1

- **GIVEN** a caller creates an extraction workflow from YAML containing
  `extraction_policy_version: v1`
- **WHEN** `create_extraction_workflow(...)` validates the source
- **THEN** the helper accepts the definition
- **AND** it preserves v1 persisted metadata in the workflow `extract` payload.

#### Scenario: Create rejects mixed metadata

- **GIVEN** a caller creates an extraction workflow from metadata-bearing YAML
  that lacks `extraction_policy_version: v1`
- **WHEN** `create_extraction_workflow(...)` validates the source
- **THEN** the helper fails before calling the workflow API
- **AND** the error identifies the source as mixed or unsupported.

#### Scenario: Legacy update without existing state is not rejected by downgrade guard

- **GIVEN** a caller updates an extraction workflow with pure legacy YAML
- **AND** the SDK helper does not have existing-workflow state
- **WHEN** `update_extraction_workflow(...)` validates the update
- **THEN** the helper does not reject the update solely because the existing
  workflow shape is unknown
- **AND** it does not perform a hidden `workflows.get(...)` preflight read solely
  to enforce downgrade safety
- **AND** server-side workflow validation remains responsible for rejecting an
  accidental v1-to-legacy downgrade when stored workflow state is available.

#### Scenario: SDK does not add client-side downgrade option in this phase

- **GIVEN** a caller updates an extraction workflow through the SDK helper
- **WHEN** the helper validates the supplied extraction definition
- **THEN** the helper does not require or expose an `allow_legacy_downgrade`
  option in this change
- **AND** it does not infer existing workflow shape from `workflow_id`
- **AND** any future client-side downgrade guard requires a separately specified
  explicit existing-workflow context surface.

### Requirement: Extraction error callback bodies preserve required identity

SDK extraction task error helpers SHALL be able to build a callback-compatible
error body from fatal task identifiers even when a full typed request object is
unavailable.

#### Scenario: Minimal fatal callback body is valid

- **GIVEN** a fatal extraction task error has a callback URL, document ID, task
  ID, code, and message
- **WHEN** the SDK error helper builds the callback body
- **THEN** the body contains `documentID`, `taskID`, `code`, and `message`
- **AND** the body is accepted by the GroundX extraction callback handler.

#### Scenario: Optional processor identity is preserved

- **GIVEN** a fatal extraction task error also has model ID or processor ID
- **WHEN** the SDK error helper builds the callback body
- **THEN** those identifiers are included when supported by the callback
  contract
- **AND** callers that only have the minimal required identifiers remain
  supported.
