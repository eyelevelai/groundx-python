# Spec delta: extraction-workflow-convenience

## ADDED Requirements

### Requirement: extraction workflow authoring submits raw YAML

The Python SDK SHALL send authored YAML unchanged to the workflow API for
create and update. It SHALL NOT compile, validate, normalize, hash, or derive
execution metadata from that YAML.

#### Scenario: create preserves YAML bytes

- **GIVEN** authored YAML text or a UTF-8 YAML file
- **WHEN** a caller creates an extraction workflow
- **THEN** the generated workflow client receives the exact YAML text
- **AND** no SDK workflow compiler runs.

#### Scenario: update preserves YAML bytes

- **GIVEN** authored YAML text or a UTF-8 YAML file
- **WHEN** a caller updates an extraction workflow
- **THEN** the generated workflow client receives the exact YAML text
- **AND** no SDK workflow compiler runs.

#### Scenario: authoring accepts one raw source

- **GIVEN** an extraction workflow create or update call
- **WHEN** neither or both of `path` and `yaml_text` are supplied
- **THEN** the SDK fails before calling the workflow API.

### Requirement: server workflow metadata remains readable

The Python SDK SHALL preserve server-supplied extraction metadata for readback
and reassembly without reconstructing authored or compiler-owned metadata.

#### Scenario: workflow readback preserves server metadata

- **GIVEN** a workflow response containing canonical extraction metadata
- **WHEN** the SDK loads that workflow for readback
- **THEN** it preserves the response metadata exactly
- **AND** it does not run an authoring compiler.

## REMOVED Requirements

### Requirement: Python SDK exposes first-class extraction definition loaders

### Requirement: Python SDK exposes extraction workflow create/update helpers

### Requirement: Extraction workflow create/update validates supported shapes
