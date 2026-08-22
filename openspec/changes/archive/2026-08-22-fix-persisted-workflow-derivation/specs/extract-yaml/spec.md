# Spec delta: extract-yaml

## ADDED Requirements

### Requirement: persisted workflow readback is not authored compilation

The SDK SHALL compile and validate authored YAML when creating a new extraction
definition. It SHALL NOT recompile the persisted extract returned by an
existing workflow. Existing-workflow readback SHALL preserve the extract,
structurally validate its execution metadata, and return `prepared=None`.

#### Scenario: historical authored snapshot remains readable

- **GIVEN** an existing workflow contains a historical authored snapshot that
  current authoring validation would reject
- **WHEN** the SDK loads that workflow for execution
- **THEN** it preserves the workflow extract without compiling the snapshot
- **AND** it returns `prepared=None`.

#### Scenario: current authoring rules do not rewrite deployed execution

- **GIVEN** an existing workflow has valid compiled execution routes
- **AND** its authored agent chain does not satisfy current authoring coverage
  rules
- **WHEN** the SDK loads the workflow
- **THEN** the deployed extract is accepted unchanged
- **AND** current authoring coverage rules are not applied.

#### Scenario: authored input still compiles

- **GIVEN** a path, YAML string, or authored mapping
- **WHEN** the SDK creates an extraction definition from it
- **THEN** the SDK applies current authored-YAML validation and compilation
- **AND** returns its prepared definition.

#### Scenario: malformed execution metadata fails

- **GIVEN** an existing workflow whose execution routes reference missing
  workflow fields
- **WHEN** the SDK loads the workflow
- **THEN** structural validation fails with a descriptive error.
