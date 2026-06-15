## ADDED Requirements

### Requirement: Extraction YAML can assign workflow groups to custom steps

The SDK SHALL support workflow metadata that assigns prepared workflow groups
to named custom workflow steps without changing the final JSON group names.
Top-level `workflow:` SHALL always be reserved for workflow authoring metadata.
Final output schemas SHALL NOT use `workflow:` as a top-level final group.

#### Scenario: Custom step assignment preserves final groups

- **GIVEN** YAML with final groups and `workflow_step` metadata assigning those
  groups to custom step names
- **WHEN** `prepare_extraction_yaml(...)` prepares the YAML
- **THEN** prepared final groups still match the real top-level final JSON
  groups
- **AND** prepared workflow groups expose the executable groups
- **AND** workflow metadata includes the custom step assignment
- **AND** pseudo/custom workflow group names do not appear as final groups

#### Scenario: Custom steps exist at each supported level

- **GIVEN** YAML with custom chunk, section, and document workflow step
  definitions
- **WHEN** the SDK prepares the YAML
- **THEN** each custom step definition is preserved with its level
- **AND** each custom step definition has `name`, `level`, `kind`, optional
  `config`, and optional `required_template_keys`
- **AND** valid level/kind combinations are `chunk` with `instruct`, `keys`, or
  `summary`; `section` with `instruct`, `keys`, or `summary`; and `document`
  with `keys` or `summary`
- **AND** optional `config` uses the existing element-targeted workflow step
  shape and omits or nulls the legacy fixed-output `field`
- **AND** workflow group assignments can point to the custom step names
- **AND** legacy fixed step names remain valid

#### Scenario: Workflow template values are not per-step metadata

- **GIVEN** YAML with workflow-level `workflow.template`
- **AND** custom step definitions with optional `required_template_keys`
- **WHEN** the SDK prepares workflow metadata
- **THEN** `workflow.template` is treated as the workflow/process template map
- **AND** `required_template_keys` is preserved as step metadata
- **AND** custom step definitions with nested per-step `template` maps fail
  clearly instead of creating per-step template behavior

#### Scenario: Legacy slot metadata remains supported

- **GIVEN** YAML that uses existing `slot:` metadata and no custom step
  definitions
- **WHEN** `prepare_extraction_yaml(...)` prepares the YAML
- **THEN** current workflow group metadata behavior remains unchanged
- **AND** callers do not need to add custom step definitions
- **AND** new documentation treats `slot:` as legacy compatibility and teaches
  `workflow_step:` as the forward path

#### Scenario: Workflow step metadata replaces slot for new YAML

- **GIVEN** YAML with a final group assigned by `workflow_step`
- **WHEN** `prepare_extraction_yaml(...)` prepares the YAML
- **THEN** the group is assigned to the canonical fixed or custom workflow step
  named by `workflow_step`
- **AND** final JSON group and field names remain unchanged

#### Scenario: Slot and workflow_step conflict fails clearly

- **GIVEN** YAML with a final group that declares both `slot` and
  `workflow_step`
- **WHEN** `prepare_extraction_yaml(...)` prepares the YAML
- **THEN** preparation fails
- **AND** the error states that only one workflow assignment key is allowed

#### Scenario: Workflow is always reserved

- **GIVEN** YAML with a top-level `workflow:` mapping
- **WHEN** `prepare_extraction_yaml(...)` prepares the YAML
- **THEN** `workflow:` is parsed only as workflow authoring metadata
- **AND** a final output group named `workflow` is rejected with a clear
  migration error

#### Scenario: Invalid custom step identity fails clearly

- **GIVEN** YAML with custom step definitions
- **AND** a custom step name is invalid, duplicated within its uniqueness scope,
  collides with a fixed workflow step name, uses a reserved name, or maps to a
  duplicate custom output destination after normalization
- **WHEN** `prepare_extraction_yaml(...)` prepares the YAML
- **THEN** preparation fails
- **AND** the error identifies the custom step and the identity rule that was
  violated
- **AND** valid custom step names match `^[a-z][a-z0-9_]{0,63}$`
- **AND** custom step names are not auto-normalized across case, kebab, snake,
  or camel forms

#### Scenario: Custom step names normalize consistently

- **GIVEN** YAML custom step names that use the allowed authoring form
- **WHEN** the SDK prepares workflow metadata and serializes workflow config
- **THEN** the same canonical step identity is used in workflow JSON, persisted
  extract metadata, custom X-Ray/readback output paths, and route metadata
- **AND** final JSON group and field names are not changed by the canonical
  workflow step identity

#### Scenario: Output keys are canonical

- **GIVEN** YAML workflow field names assigned to custom steps
- **WHEN** SDK preparation creates custom output route metadata
- **THEN** an `output_key` defaults to the prepared workflow field name only
  when the field name matches `^[a-z][a-z0-9_]{0,63}$`
- **AND** invalid or nested workflow field names require an explicit valid
  field-level `workflow_output_key` beside the prompted field definition
- **AND** `workflow_output_key` is authoring-only metadata that is persisted as
  route `output_key`, exposed in public JSON `outputRoutes[]` records as
  `outputKey`, and never emitted as a final JSON field
- **AND** duplicate `(output_map, step_name, output_key)` destinations fail
- **AND** duplicate final JSON field routes fail

### Requirement: Persisted workflow extract preserves custom step metadata

The SDK SHALL preserve custom step definitions and workflow group assignments in
the JSON-serializable persisted workflow extract payload. The payload SHALL
include `workflow.metadata_version: 1` and enough canonical schema and route
metadata for the public API/runtime to derive or verify per-executable-step field
counts. The field-count metadata SHALL use the canonical `leaf_fields` shape
defined by the workflow-config contract.

#### Scenario: Custom step metadata survives workflow extract round trip

- **GIVEN** YAML with custom step definitions and workflow group assignments
- **WHEN** the SDK prepares the YAML and serializes
  `PreparedExtractionYaml.persisted_workflow_extract`
- **AND** the serialized mapping is prepared again
- **THEN** the custom step definitions are still present
- **AND** the workflow group assignments are still present
- **AND** final groups, workflow groups, and route metadata still match the
  original preparation
- **AND** `leaf_fields` are derived from the YAML final schema and workflow
  assignments using the workflow-config `leaf_fields` contract
- **AND** derived `output_routes` and `leaf_fields` have a one-to-one match on
  `final_path`, `workflow_group`, `workflow_field`, `step_name`, `level`, and
  `output_key`
- **AND** repeated item/object leaves use the workflow-config wildcard
  schema path convention, such as `/fees/*/amount`
- **AND** per-executable-step field counts can be derived or verified from the
  persisted metadata without trusting caller-provided count fields alone
- **AND** no executable workflow step is assigned more than 20 fields

#### Scenario: Persisted workflow extract version compatibility is explicit

- **GIVEN** a persisted workflow extract payload with missing, current, unknown,
  or future-version custom workflow metadata
- **WHEN** the SDK prepares that mapping input again
- **THEN** `workflow.metadata_version: 1` metadata is loaded
- **AND** missing `workflow:` metadata follows legacy fixed-step fallback only
  when no custom steps, output routes, or custom output maps are present
- **AND** missing metadata version fails when custom workflow metadata is present
- **AND** unknown, future, non-integer, or unsupported versions fail closed
- **AND** the result never silently drops custom step assignments
