# custom-workflow-step-authoring Specification

## Purpose
TBD - created by archiving change age-148-adp-workflow-needs-more-extraction-step-capacity-than-fixed. Update Purpose after archive.
## Requirements
### Requirement: PreparedExtractionYaml carries custom-step and template fields
`PreparedExtractionYaml` SHALL expose four new optional fields — `custom_template`,
`custom_steps`, `output_routes`, and `leaf_fields` — that are populated by
`prepare_extraction_yaml` when the authored YAML contains the corresponding top-level
keys (`_template`, `_custom_steps`, `_output_routes`, `_leaf_fields`). All four fields
default to empty / None and are ignored when absent.

#### Scenario: Custom steps and template round-trip through persisted extract
- **WHEN** a YAML document contains `_template`, `_custom_steps`, `_output_routes`, and
  `_leaf_fields` top-level keys alongside ordinary group definitions
- **THEN** `prepare_extraction_yaml` returns a `PreparedExtractionYaml` whose
  `custom_template`, `custom_steps`, `output_routes`, and `leaf_fields` fields are
  populated with the authored values
- **AND** the `persisted_workflow_extract` mapping includes the original top-level keys
  so a subsequent `prepare_extraction_yaml` on that mapping recovers the same values

#### Scenario: YAML without custom-step keys produces no custom fields
- **WHEN** a YAML document contains only ordinary group definitions with no
  `_template`, `_custom_steps`, `_output_routes`, or `_leaf_fields` keys
- **THEN** `prepare_extraction_yaml` returns a `PreparedExtractionYaml` with
  `custom_template` as `None` and `custom_steps`, `output_routes`, `leaf_fields` as
  empty lists
- **AND** existing group, workflow-group, and field-path behavior is unchanged

### Requirement: prepare_extraction_yaml validates custom-step fields at parse time
The `prepare_extraction_yaml` function SHALL validate each entry in `_custom_steps`
against the `CustomWorkflowStep` contract before returning:
- `name` MUST match the pattern `^[a-z][a-z0-9_]{0,63}$`
- `level` MUST be one of `chunk`, `section`, or `document`
- `kind` MUST be one of `instruct`, `keys`, or `summary`

Invalid values SHALL raise `ValueError` with a message that includes the step name and
the invalid field, before the caller can submit the workflow request.

#### Scenario: Invalid step name is rejected at parse time
- **WHEN** `_custom_steps` contains an entry whose `name` is `"bad name"` (contains a space)
- **THEN** `prepare_extraction_yaml` raises `ValueError` naming the invalid `name` value
- **AND** no `PreparedExtractionYaml` is returned

#### Scenario: Invalid level enum is rejected at parse time
- **WHEN** `_custom_steps` contains an entry whose `level` is `"paragraph"` (not in enum)
- **THEN** `prepare_extraction_yaml` raises `ValueError` naming the invalid `level` value
- **AND** no `PreparedExtractionYaml` is returned

#### Scenario: Invalid kind enum is rejected at parse time
- **WHEN** `_custom_steps` contains an entry whose `kind` is `"embed"` (not in enum)
- **THEN** `prepare_extraction_yaml` raises `ValueError` naming the invalid `kind` value
- **AND** no `PreparedExtractionYaml` is returned

#### Scenario: Valid custom step passes validation
- **WHEN** `_custom_steps` contains an entry with `name: "adp_chunk_01"`, `level: "chunk"`,
  `kind: "instruct"`
- **THEN** `prepare_extraction_yaml` returns successfully with that step in `custom_steps`
- **AND** the step name pattern `^[a-z][a-z0-9_]{0,63}$` is satisfied

### Requirement: PromptManager passes custom-step fields to WorkflowRequest at submit
The `PromptManager` SHALL read `custom_template`, `custom_steps`, `output_routes`, and
`leaf_fields` from the prepared `PreparedExtractionYaml` and include them as the
corresponding optional fields (`template`, `customSteps`, `outputRoutes`, `leafFields`)
in the `WorkflowRequest` or workflow-update payload it builds. When these fields are
absent or empty they SHALL be omitted from the payload.

#### Scenario: Custom steps included in workflow create payload
- **WHEN** `PromptManager.persisted_workflow_extract_dict` is called for a workflow whose
  YAML contains `_custom_steps` with one valid step
- **THEN** the `persisted_workflow_extract` mapping contains the `_custom_steps` key so
  callers assembling a `WorkflowRequest` can include `customSteps`
- **AND** the mapping is JSON-serializable

#### Scenario: Empty custom steps omitted from payload
- **WHEN** a workflow YAML contains no `_custom_steps` key
- **THEN** the `persisted_workflow_extract` mapping contains no `_custom_steps` key
- **AND** callers assembling a `WorkflowRequest` set `customSteps` to `None` / omit it

#### Scenario: Custom steps survive the workflow extract round-trip
- **WHEN** a `WorkflowDetail.extract` mapping (as returned by `gx_client.workflows.get`)
  contains a `_groundx_persisted_extract` blob that itself contains `_custom_steps`
- **THEN** `prepare_extraction_yaml` on that mapping recovers the same `custom_steps` list
- **AND** the recovered step names, levels, and kinds match the original authored values

### Requirement: Backward-compatibility — fixed-slot paths unchanged by custom-step addition
Adding custom-step fields to `PreparedExtractionYaml` and the workflow payload SHALL NOT
alter the behavior of any existing fixed-slot code path.

#### Scenario: Existing workflow without custom steps continues to work
- **WHEN** a `WorkflowDetail.extract` mapping contains no `_custom_steps`, `_template`,
  `_output_routes`, or `_leaf_fields` keys
- **THEN** `prepare_extraction_yaml` returns a `PreparedExtractionYaml` with the same
  `groups`, `workflow_groups`, and `workflow_field_paths` as before this change
- **AND** `PromptManager.workflow_extract_dict` returns the same dict it returned before
  this change

