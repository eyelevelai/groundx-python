## ADDED Requirements

### Requirement: Template workflow config is exposed

The public workflow config SHALL expose the existing runtime `template` setting
so SDK callers can supply prompt template values. The public shape SHALL follow
the cashbot-go workflow/process runtime model, where `Process.Template` is a
`map[string]string` consumed by prompt rendering, and SHALL NOT reuse or blur
the separate partner request template object.

#### Scenario: Template mapping remains workflow-level metadata

- **GIVEN** workflow/process config with a `template` mapping
- **WHEN** the SDK serializes the workflow request
- **THEN** the mapping is sent as workflow-level config
- **AND** it is not treated as an extraction YAML final group
- **AND** it can be used by fixed and custom workflow step prompts

#### Scenario: Template compatibility path follows Process.Template

- **GIVEN** the public workflow API exposes workflow create and update requests
- **WHEN** workflow config includes `template`
- **THEN** `template` is accepted as workflow/process config matching runtime
  `Process.Template *map[string]string`
- **AND** the contract does not expose `template` as a top-level partner
  create/update compatibility field
- **AND** a top-level partner template object cannot be silently accepted as the
  workflow prompt-variable map

#### Scenario: Template config has safe public boundaries

- **GIVEN** workflow config with `template` values
- **WHEN** the request is validated, persisted, loaded, and rendered into fixed
  or custom prompts
- **THEN** `template` is a map of string keys to string values
- **AND** keys are supplied without braces or normalized after accepting optional
  surrounding `{{...}}`
- **AND** keys match `^[A-Za-z][A-Za-z0-9_]{0,63}$` after brace normalization
- **AND** keys with the reserved `GROUNDX_` prefix or workflow metadata names
  fail validation
- **AND** documented system prompt keys such as `LANGUAGE` and
  `PAGE_NUMBERS_*` may be overridden
- **AND** extra keys are allowed
- **AND** required template keys are declared explicitly on workflow step config
  as `requiredTemplateKeys` in public JSON and `required_template_keys` in
  persisted metadata
- **AND** required template keys use the same brace normalization, key regex,
  reserved `GROUNDX_` prefix rule, and workflow metadata reserved-name checks as
  `template` keys
- **AND** duplicate required template keys after normalization fail validation
- **AND** missing declared required template keys fail clearly before rendering
- **AND** reserved workflow metadata names are exactly `workflow`, `steps`,
  `custom_steps`, `customSteps`, `template`, `runtime`, `output_routes`,
  `outputRoutes`, `leaf_fields`, `leafFields`, `field_counts`, `fieldCounts`,
  `schema_hash`, `schemaHash`, `metadata_version`, `metadataVersion`,
  `workflow_group`, `workflowGroup`, `workflow_field`, `workflowField`,
  `final_path`, `finalPath`, `step_name`, `stepName`, `output_key`, `outputKey`,
  `readback_path`, `readbackPath`, `_defs`, `_pseudo_groups`, and
  `_groundx_persisted_extract`
- **AND** unresolved optional placeholders keep existing fixed-prompt rendering
  behavior
- **AND** the total serialized template payload is at most 16 KiB
- **AND** each value is at most 4 KiB
- **AND** template values cannot be interpreted as extraction YAML final groups
  or custom step definitions

### Requirement: Oversized executable steps are rejected by validation

The custom-step contract SHALL define and enforce a maximum load of 20 fields
per executable workflow step in the public API/runtime path and mirror that rule
in SDK, harness, and ADP validation. Direct API callers SHALL NOT bypass the
limit.

#### Scenario: ADP-style single-step overload is rejected

- **GIVEN** YAML that assigns an excessive number of fields to one executable
  workflow step
- **WHEN** the configured validation layer evaluates the YAML
- **THEN** the validation fails
- **AND** the message names the overloaded workflow step
- **AND** the message states that one executable workflow step may own at most
  20 fields
- **AND** the message recommends splitting the fields across custom steps

#### Scenario: Direct API callers cannot bypass the field-load guardrail

- **GIVEN** a workflow create or update request sent through the public API or
  generated SDK without using harness or ADP validation
- **AND** the request assigns an excessive number of fields to one executable
  workflow step
- **WHEN** the configured validation layer evaluates the request
- **THEN** the request fails before runtime execution
- **AND** the error identifies the overloaded workflow step
- **AND** the error identifies the 20-field limit

#### Scenario: Field-load validation derives or verifies persisted metadata

- **GIVEN** a workflow create or update request with custom extraction steps
- **WHEN** the public API/runtime validates executable-step field load
- **THEN** the field counts are derived from canonical persisted
  `workflow.extract.workflow.output_routes` and
  `workflow.extract.workflow.leaf_fields`, or verified through a
  server-recomputable integrity record over that same metadata
- **AND** the counts use the same canonical custom step identities as workflow
  config and route metadata
- **AND** caller-provided field counts are never authoritative by themselves
- **AND** requests with missing, unparseable, stale, caller-only, mismatched, or
  unknown-version field-count metadata fail before runtime execution
- **AND** the server counts distinct final leaf field routes assigned to each
  executable workflow step
- **AND** repeated/list field definitions count as one field definition unless
  they introduce separate prompted leaf fields
- **AND** optional `field_counts` and `schema_hash` values are treated as hints
  that must match the server-recomputed counts and canonical hash when present
- **AND** the canonical hash is SHA-256 over sorted-key, no-whitespace canonical
  JSON using persisted snake_case keys
- **AND** canonical arrays are sorted ascending by deterministic identity tuples:
  `custom_steps` by `(name)`, `output_routes` by `(final_path, workflow_group,
  workflow_field, step_name, output_key)`, and `leaf_fields` by `(final_path,
  workflow_group, workflow_field, step_name, output_key)`
- **AND** the canonical hash input contains exactly `metadata_version`,
  `custom_steps`, `output_routes`, and `leaf_fields`
- **AND** each `custom_steps` record contains `name`, `level`, `kind`, and any
  declared `required_template_keys`
- **AND** each `leaf_fields` record contains `final_path`, `workflow_group`,
  `workflow_field`, `step_name`, `level`, `output_key`, `field_type`,
  `is_repeated`, and `repetition_scope`
- **AND** `is_repeated` is a boolean
- **AND** `repetition_scope` is one of `none`, `field`, or `item`
- **AND** `none` is valid only when `is_repeated` is false
- **AND** `field` means a repeated/list value is prompted as one leaf and counts
  as one field for the executable step
- **AND** `item` means repeated item/object schema introduces separate prompted
  leaves, and each prompted item leaf appears as its own `leaf_fields` record at
  its full schema-level final path
- **AND** `item` leaf final paths use a literal `*` RFC 6901 path segment at each
  repeated-item boundary, such as `/fees/*/amount`
- **AND** the `*` segment is a schema wildcard, not a runtime array index
- **AND** wildcard item leaf paths count once per prompted schema leaf rather
  than once per runtime array element
- **AND** invalid `is_repeated` and `repetition_scope` combinations fail before
  hashing or execution
- **AND** prompt prose, examples, model parameters, template values, and other
  data that does not affect executable-step field load are excluded from the
  field-count hash
- **AND** every `output_routes` record has exactly one matching `leaf_fields`
  record with the same `final_path`, `workflow_group`, `workflow_field`,
  `step_name`, `level`, and `output_key`
- **AND** every `leaf_fields` record has exactly one matching `output_routes`
  record with the same identity
- **AND** matched `leaf_fields` records must match the final extract schema's
  prompted leaf at `final_path`, including `field_type`, `is_repeated`, and
  `repetition_scope`
- **AND** missing, extra, duplicate, stale, or mismatched route/leaf records fail
  before field-count hashing or execution

#### Scenario: Spoofed field-count metadata is rejected

- **GIVEN** a workflow create or update request with custom extraction steps
- **AND** the request provides field-count metadata that claims the step is under
  the configured limit
- **AND** canonical `workflow.extract.workflow.output_routes` and
  `workflow.extract.workflow.leaf_fields` show the step is oversized
- **WHEN** the public API/runtime validates executable-step field load
- **THEN** the request fails before runtime execution
- **AND** the error identifies the overloaded workflow step and the metadata
  mismatch

### Requirement: Custom step support keeps fixed workflow defaults

Custom step support SHALL be additive to the existing fixed workflow-step
contract.

#### Scenario: Existing fixed workflow steps still work

- **GIVEN** a workflow using only existing fixed `WorkflowSteps` fields
- **WHEN** the workflow is created, updated, loaded, and processed
- **THEN** existing fixed-step behavior remains unchanged
- **AND** existing tests for `chunk-instruct`, `chunk-keys`,
  `chunk-summary`, section, and document steps continue to pass

### Requirement: Custom workflow steps are workflow-level config

The public workflow config SHALL expose custom workflow steps through a
workflow-level `customSteps` array while preserving the legacy fixed `steps`
object.

#### Scenario: Custom steps are separate from fixed steps

- **GIVEN** workflow config with legacy fixed `steps`
- **AND** workflow config with custom step definitions
- **WHEN** the SDK serializes and the runtime validates the workflow
- **THEN** legacy fixed steps remain under `steps`
- **AND** custom step definitions are serialized under `customSteps`
- **AND** each custom step record contains `name`, `level`, `kind`, optional
  `config`, and optional `requiredTemplateKeys`
- **AND** valid `level` values are `chunk`, `section`, and `document`
- **AND** valid level/kind combinations are `chunk` with `instruct`, `keys`, or
  `summary`; `section` with `instruct`, `keys`, or `summary`; and `document`
  with `keys` or `summary`
- **AND** invalid level/kind combinations fail validation
- **AND** optional `config` uses the existing element-targeted workflow step
  shape with element keys `all`, `figure`, `json`, `paragraph`, `table`, and
  `table-figure`
- **AND** custom step element config may carry existing prompt, engine, and
  include settings
- **AND** custom step element config omits or nulls the legacy fixed-output
  `field` because custom output storage is derived from `level`, `kind`,
  `outputRoutes`, and `leafFields`
- **AND** persisted `workflow.extract.workflow.custom_steps[]` uses snake_case
  `required_template_keys` for the same logical step-level required template keys
- **AND** custom step names are not parsed as fixed `WorkflowSteps` enum keys

#### Scenario: Custom step names are canonical

- **GIVEN** workflow config with custom step definitions
- **WHEN** names are validated
- **THEN** custom step names match `^[a-z][a-z0-9_]{0,63}$`
- **AND** names are globally unique across all custom levels
- **AND** uppercase, hyphenated, dotted, spaced, leading-underscore, or
  trailing-underscore names fail instead of being auto-normalized
- **AND** names that collide with fixed step names, fixed snake_case aliases, or
  reserved workflow/runtime keys fail validation
- **AND** the canonical step identity is exactly the authored lower-snake-case
  value

### Requirement: Custom output routes are workflow-level config

The public workflow config SHALL expose custom output route records through a
workflow-level `outputRoutes` array. `outputRoutes` is the public camelCase
representation of persisted `workflow.extract.workflow.output_routes`.

#### Scenario: Direct public route records are explicit

- **GIVEN** a direct workflow create or update request with custom workflow steps
- **WHEN** the request defines custom output routes without using YAML preparation
- **THEN** the routes are serialized under workflow-level `outputRoutes`
- **AND** each route includes `workflowGroup`, `workflowField`, `finalPath`,
  `stepName`, `level`, `outputMap`, `outputKey`, and `readbackPath`
- **AND** `outputKey` follows the same lower-snake-case rule as persisted
  `output_key`
- **AND** `finalPath` is an RFC 6901 JSON Pointer
- **AND** `level` is one of `chunk`, `section`, or `document`
- **AND** `outputMap` matches `level`: `customChunkOutputs` for `chunk`,
  `customSectionOutputs` for `section`, and `customDocumentOutputs` for
  `document`
- **AND** `readbackPath` uses the canonical non-page template for the output
  level
- **AND** duplicate final paths fail validation
- **AND** duplicate `(outputMap, stepName, outputKey)` destinations fail
- **AND** each route must have exactly one matching `leafFields` record with the
  same `finalPath`, `workflowGroup`, `workflowField`, `stepName`, `level`, and
  `outputKey`
- **AND** the runtime persists the routes as snake_case
  `workflow.extract.workflow.output_routes`
- **AND** requests with custom workflow outputs but no derivable or supplied
  `outputRoutes` fail before execution

### Requirement: Custom leaf fields are workflow-level config

The public workflow config SHALL expose custom workflow leaf-field metadata
through a workflow-level `leafFields` array when the caller bypasses YAML
preparation. `leafFields` is the public camelCase representation of persisted
`workflow.extract.workflow.leaf_fields`.

#### Scenario: Direct public leaf-field records are explicit

- **GIVEN** a direct workflow create or update request with custom workflow steps
- **WHEN** the request defines custom output routes without using YAML preparation
- **THEN** the request supplies workflow-level `leafFields`, or the runtime can
  derive equivalent `leaf_fields` from canonical persisted metadata
- **AND** each public `leafFields` record includes `finalPath`, `workflowGroup`,
  `workflowField`, `stepName`, `level`, `outputKey`, `fieldType`, `isRepeated`,
  and `repetitionScope`
- **AND** public `isRepeated` maps to persisted `is_repeated`
- **AND** public `repetitionScope` maps to persisted `repetition_scope`
- **AND** each `leafFields` record must have exactly one matching `outputRoutes`
  record with the same `finalPath`, `workflowGroup`, `workflowField`,
  `stepName`, `level`, and `outputKey`
- **AND** each `leafFields` record must match the final extract schema's prompted
  leaf at `finalPath`, including `fieldType`, `isRepeated`, and
  `repetitionScope`
- **AND** extra, missing, duplicate, stale, or mismatched `leafFields` records
  fail validation
- **AND** requests with custom workflow steps but no derivable or supplied
  `leafFields` fail before execution
