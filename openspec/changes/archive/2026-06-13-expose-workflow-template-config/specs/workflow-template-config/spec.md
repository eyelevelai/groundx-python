## ADDED Requirements

### Requirement: Public workflow contract exposes workflow template

The public workflow create/update request and workflow detail response contract SHALL expose workflow-level `template` values as a first-class workflow config field.

#### Scenario: Workflow create/update request accepts template

- **GIVEN** a caller creates or updates a workflow through the public workflow
  API
- **WHEN** the request body includes `template`
- **THEN** the API contract accepts `template` as an object
- **AND** each template value is a string
- **AND** the backend workflow request path stores those values on the workflow
  process template rather than dropping or mis-decoding them
- **AND** production backend request parsing preserves those values before the
  workflow handler runs
- **AND** a create request with `template` as the only workflow process setting
  succeeds
- **AND** an update request with `workflowId` plus `template` as the only
  workflow process setting succeeds
- **AND** the field is documented as workflow-level prompt template values used
  by workflow step prompts
- **AND** existing `name`, `extract`, `steps`, `chunkStrategy`, and
  `sectionStrategy` request fields remain unchanged

#### Scenario: Workflow template rejects non-string values

- **GIVEN** a caller creates or updates a workflow through the public workflow
  API
- **WHEN** the request body includes `template` with any non-string value
- **THEN** production backend request parsing rejects the request
- **AND** the workflow is not created or updated
- **AND** the invalid workflow template is not silently dropped

#### Scenario: Workflow template update follows process overlay semantics

- **GIVEN** a stored workflow already has workflow-level template values
- **WHEN** a caller updates the workflow with a non-empty `template` object
- **THEN** matching template keys are overwritten by the update
- **AND** unrelated existing template keys are preserved
- **AND** omitting `template` from a later workflow update leaves stored
  template values unchanged
- **AND** clear/delete semantics for template keys are not introduced by this
  template-only change

#### Scenario: Existing non-workflow template routes are preserved

- **GIVEN** the backend shared request model already uses the JSON field name
  `template` for non-workflow routes
- **WHEN** workflow template support is added
- **THEN** existing non-workflow template request decoding continues to work
- **AND** workflow create/update requests with top-level `template` are routed
  into workflow process template settings
- **AND** the shared backend request struct does not add duplicate
  `json:"template"` fields
- **AND** any workflow-template sidecar field on the shared request struct is
  not itself bound to the JSON name `template`

#### Scenario: Workflow detail returns template

- **GIVEN** a workflow was created or updated with workflow-level template
  values
- **WHEN** a caller fetches or receives workflow detail
- **THEN** the workflow detail contract includes `template`
- **AND** generated SDKs expose the field as a declared generated model
  property rather than relying on permissive extra-field behavior
- **AND** workflows without `template` continue to deserialize successfully

#### Scenario: Template slice does not expose custom workflow steps

- **GIVEN** this change is intended as a small template-only release
- **WHEN** the public workflow contract is updated
- **THEN** the change does not add `customSteps`
- **AND** the change does not add `outputRoutes`
- **AND** the change does not add `leafFields`
- **AND** the change does not add custom output readback schemas
- **AND** the larger custom workflow-step contract remains a separate plan

### Requirement: Generated SDK work waits for Fern publication

The Python SDK SHALL consume the workflow-template field only after the Fern
contract update has been published or otherwise delivered through the approved
generation path.

#### Scenario: Python SDK generation follows Fern

- **GIVEN** `groundx-python` workflow client files are Fern-generated
- **WHEN** workflow `template` support is added
- **THEN** generated files are not hand-edited before the Fern update is
  published
- **AND** the SDK change includes tests proving create, update, declared model
  fields, and workflow detail readback support after regeneration
- **AND** any handwritten SDK tests added under `tests/custom` are protected by
  `.fernignore`
- **AND** the SDK change remains independent from extraction workflow
  convenience methods

### Requirement: Harness YAML passthrough is optional and template-only

GroundX Studio Harness SHALL keep authored extraction YAML `workflow.template` passthrough optional and template-only when that consumer phase is approved.

#### Scenario: Harness compiler preserves workflow template

- **GIVEN** an authored extraction YAML includes `workflow.template`
- **WHEN** the harness compiler builds workflow artifacts
- **THEN** the compiled workflow JSON includes top-level `template`
- **AND** executable extract groups do not accidentally retain control metadata
  as extraction fields
- **AND** the compiler does not require custom workflow-step metadata

#### Scenario: Harness deploy passes template through

- **GIVEN** compiled workflow JSON contains top-level `template`
- **WHEN** the harness deploy script creates or updates a workflow
- **THEN** it passes `template` to the generated workflow client only when the
  installed SDK surface supports the argument
- **AND** it fails clearly before the workflow API call when an older SDK would
  otherwise drop or reject the template argument
- **AND** it does not pass `customSteps`, `outputRoutes`, or `leafFields`
