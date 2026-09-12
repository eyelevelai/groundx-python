## ADDED Requirements

### Requirement: Saved revisions load through existing SDK helpers
The sync and async workflow-backed loaders SHALL accept optional revision_id and return the saved canonical extraction definition without recompilation.

#### Scenario: Exact historical read

- **WHEN** the caller selects A while B is current
- **THEN** the helper calls the generated revision read for A and returns A's saved extract with prepared=None.

#### Scenario: Invalid selector

- **WHEN** revision_id is empty or supplied without workflow_id
- **THEN** the helper raises ValueError before HTTP.

#### Scenario: Historical read fails

- **WHEN** the revision endpoint returns an error or mismatched identity
- **THEN** the error is exposed and the helper never fetches the current workflow as a fallback.

### Requirement: Updates preserve concurrency and authored source
Both raw-YAML update helpers SHALL forward supplied expected_updated_at unchanged while preserving existing omission and request-option semantics.

#### Scenario: Caller guards an update

- **WHEN** YAML and expected_updated_at are supplied
- **THEN** the generated request carries the original source bytes and the same token.

#### Scenario: Existing caller omits the token

- **WHEN** update_extraction_workflow is called without expected_updated_at
- **THEN** no token is fabricated and the existing call remains supported.

### Requirement: Generated and preserved surfaces remain distinct
SDK implementation SHALL keep generated API changes in Fern and regression coverage in protected handwritten paths.

#### Scenario: SDK regeneration

- **WHEN** the matching Fern schema generates clients
- **THEN** the helper implementation, tests, and this OpenSpec survive through .fernignore and both sync and async behavior remain covered.
