## ADDED Requirements

### Requirement: Extraction YAML can author custom workflow steps

The SDK SHALL parse top-level `workflow:` authoring metadata for custom
workflow steps while preserving final JSON group names.

#### Scenario: Custom workflow steps prepare into persisted metadata

- **GIVEN** extraction YAML with `workflow.custom_steps`, workflow-level
  `workflow.template`, final groups, group-level `workflow_step`, and
  field-level `workflow_output_key`
- **WHEN** `prepare_extraction_yaml(...)` prepares the YAML
- **THEN** final groups remain the final JSON shape
- **AND** custom step definitions are persisted under
  `workflow.extract.workflow.custom_steps`
- **AND** route metadata is persisted under
  `workflow.extract.workflow.output_routes`
- **AND** leaf metadata is persisted under
  `workflow.extract.workflow.leaf_fields`
- **AND** the final JSON does not contain the authoring-only `workflow`,
  `workflow_step`, or `workflow_output_key` metadata keys

#### Scenario: Workflow is always reserved

- **GIVEN** YAML with a top-level `workflow:` mapping
- **WHEN** `prepare_extraction_yaml(...)` prepares the YAML
- **THEN** the mapping is parsed only as workflow authoring metadata
- **AND** a final output group named `workflow` is rejected with a clear
  migration error

#### Scenario: Legacy slot remains compatibility-only

- **GIVEN** legacy YAML that uses `slot:` metadata and no custom step
  definitions
- **WHEN** `prepare_extraction_yaml(...)` prepares the YAML
- **THEN** existing fixed-step behavior remains unchanged
- **AND** new YAML may use `workflow_step:` for fixed or custom step names
- **AND** a group that declares both `slot` and `workflow_step` fails clearly

#### Scenario: Custom step identity is canonical

- **GIVEN** YAML custom step definitions
- **WHEN** the SDK prepares workflow metadata
- **THEN** custom step names match `^[a-z][a-z0-9_]{0,63}$`
- **AND** names are globally unique across custom steps
- **AND** names do not collide with fixed workflow step names or reserved
  metadata names
- **AND** uppercase, hyphenated, dotted, spaced, leading-underscore, empty, or
  overlength names fail clearly

#### Scenario: Field load is mirrored before workflow submission

- **GIVEN** prepared YAML that assigns more than 20 prompted leaf fields to one
  executable workflow step
- **WHEN** the SDK prepares or submits the workflow
- **THEN** the SDK raises an error naming the overloaded step
- **AND** the error states that one executable workflow step may own at most 20
  fields
- **AND** public API/runtime validation remains authoritative for direct API
  callers

### Requirement: Persisted workflow extract keeps custom metadata round trippable

The SDK SHALL persist enough canonical metadata under
`workflow.extract.workflow` to reload authored custom workflow steps and derive
or verify executable-step field counts.

#### Scenario: Custom workflow extract round trips

- **GIVEN** prepared YAML with custom steps, output routes, leaf fields,
  repeated item paths, and workflow-level template values
- **WHEN** the SDK serializes and reloads
  `PreparedExtractionYaml.persisted_workflow_extract`
- **THEN** `workflow.metadata_version: 1` is preserved
- **AND** `custom_steps`, `output_routes`, and `leaf_fields` are preserved
- **AND** each route has exactly one matching leaf field on `final_path`,
  `workflow_group`, `workflow_field`, `step_name`, `level`, and `output_key`
- **AND** repeated item leaf paths use a literal `*` RFC 6901 path segment
- **AND** deterministic `schema_hash` calculation excludes prompt prose,
  examples, model parameters, and template values

#### Scenario: Unknown custom metadata versions fail closed

- **GIVEN** a persisted workflow extract payload with custom workflow metadata
- **AND** its metadata version is missing, unknown, future, non-integer, or
  unsupported
- **WHEN** the SDK reloads the mapping
- **THEN** reload fails clearly
- **AND** the SDK does not silently drop custom step assignments
