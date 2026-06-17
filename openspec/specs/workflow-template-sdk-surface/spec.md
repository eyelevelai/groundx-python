# workflow-template-sdk-surface Specification

## Purpose
TBD - created by archiving change age-149-expose-workflow-template-config-through-the-public-workflow. Update Purpose after archive.
## Requirements
### Requirement: WorkflowTemplate type alias is present and correctly typed
The Python SDK SHALL expose `WorkflowTemplate = typing.Dict[str, str]` as a named public
type alias in `src/groundx/types/` after Fern regen from the updated `eyelevel-fern-config`
OpenAPI spec, and SHALL re-export it from `src/groundx/types/__init__.py`.
The type SHALL be importable as `from groundx.types import WorkflowTemplate`.
The alias SHALL accept only `str` keys and `str` values; non-string values are not
accepted by the type system (mypy SHALL flag them as type errors).

#### Scenario: WorkflowTemplate is importable from the SDK public types namespace
- **WHEN** a caller imports `from groundx.types import WorkflowTemplate`
- **THEN** the import succeeds without error
- **AND** `WorkflowTemplate` is equivalent to `typing.Dict[str, str]`

#### Scenario: WorkflowTemplate rejects non-string values at the type-check level
- **WHEN** a caller assigns `{"key": 123}` to a variable annotated as `WorkflowTemplate`
- **THEN** `poetry run mypy .` reports a type error on that assignment
- **AND** no runtime exception is raised during the type-check step itself

#### Scenario: WorkflowTemplate accepts a valid string-to-string mapping
- **WHEN** a caller assigns `{"prompt_lang": "en", "tone": "formal"}` to a variable annotated as `WorkflowTemplate`
- **THEN** `poetry run mypy .` reports no type error for that assignment

### Requirement: WorkflowRequest exposes an optional template field on create
After Fern regen, `WorkflowRequest` SHALL include `template: typing.Optional[WorkflowTemplate] = None`.
The `WorkflowsClient.create(...)` method SHALL accept `template` as an optional keyword
argument. Passing `template=None` or omitting `template` SHALL be equivalent (field absent
from the serialized JSON payload). Passing a `dict[str, str]` SHALL serialize the mapping
as the JSON key `"template"` at the top level of the request body.

#### Scenario: create() accepts template as a keyword argument with a string map
- **WHEN** `client.workflows.create(template={"lang": "en"})` is called
- **THEN** the HTTP request body contains `"template": {"lang": "en"}` at the top level
- **AND** the call does not raise a TypeError or AttributeError

#### Scenario: create() omits template from the serialized body when not provided
- **WHEN** `client.workflows.create()` is called without the `template` argument
- **THEN** the serialized JSON body does NOT contain the key `"template"`

#### Scenario: create() omits template from the serialized body when explicitly None
- **WHEN** `client.workflows.create(template=None)` is called
- **THEN** the serialized JSON body does NOT contain the key `"template"`

#### Scenario: WorkflowRequest template passes mypy type check with a valid dict
- **WHEN** a WorkflowRequest is constructed with `template={"key": "value"}`
- **THEN** `poetry run mypy .` reports no type error for the construction

### Requirement: WorkflowRequest exposes an optional template field on update
After Fern regen, `WorkflowsClient.update(id, ...)` SHALL accept `template` as an optional
keyword argument with the same type and serialization contract as create. Omitting
`template` or passing `template=None` SHALL result in an absent JSON key, which per the
backend contract is a no-op that preserves existing stored template keys. Passing an
empty dict `{}` SHALL also be a no-op (no keys overlaid). Passing a non-empty
`dict[str, str]` SHALL serialize to `"template": {...}` and the backend will apply a
per-key overlay.

#### Scenario: update() accepts template as a keyword argument
- **WHEN** `client.workflows.update(id="wf-id", template={"tone": "neutral"})` is called
- **THEN** the HTTP request body contains `"template": {"tone": "neutral"}` at the top level
- **AND** the call does not raise a TypeError or AttributeError

#### Scenario: update() omits template from the serialized body when not provided
- **WHEN** `client.workflows.update(id="wf-id")` is called without `template`
- **THEN** the serialized JSON body does NOT contain the key `"template"`

#### Scenario: update() serializes an empty dict as template
- **WHEN** `client.workflows.update(id="wf-id", template={})` is called
- **THEN** the serialized JSON body contains `"template": {}` or omits it
- **AND** the call does not raise a TypeError or AttributeError

### Requirement: WorkflowDetail exposes an optional template field on read
After Fern regen, `WorkflowDetail` SHALL include `template: typing.Optional[WorkflowTemplate] = None`.
`template` SHALL be `None` when the response JSON omits or nulls the key.
When the response JSON includes `"template": {"key": "val"}`, `workflow_detail.template`
SHALL equal `{"key": "val"}` as a `dict[str, str]`.
The `template` attribute SHALL be accessible on the `WorkflowDetail` objects returned
by `create`, `update`, and `get` without raising `AttributeError`.

#### Scenario: WorkflowDetail.template is None when API response omits the field
- **WHEN** a `GET /v1/workflow/{id}` response body does not include `"template"`
- **THEN** the resulting `WorkflowDetail.template` is `None`
- **AND** accessing `.template` does not raise `AttributeError`

#### Scenario: WorkflowDetail.template contains the map when API response includes it
- **WHEN** a `GET /v1/workflow/{id}` response body includes `"template": {"prompt_lang": "en"}`
- **THEN** the resulting `WorkflowDetail.template` equals `{"prompt_lang": "en"}`
- **AND** its type is compatible with `WorkflowTemplate` (`dict[str, str]`)

#### Scenario: WorkflowDetail.template is populated from a create response
- **WHEN** `client.workflows.create(template={"lang": "fr"})` returns a `WorkflowResponse`
- **AND** the response body includes `"template": {"lang": "fr"}`
- **THEN** `response.workflow.template` equals `{"lang": "fr"}`

#### Scenario: WorkflowDetail.template is populated from an update response
- **WHEN** `client.workflows.update(id="wf-id", template={"tone": "formal"})` returns a `WorkflowResponse`
- **AND** the response body includes `"template": {"tone": "formal"}`
- **THEN** `response.workflow.template` equals `{"tone": "formal"}`

### Requirement: AsyncWorkflowsClient mirrors the sync template surface
The async client (`AsyncWorkflowsClient`) SHALL expose the same `template` keyword argument
on `create(...)` and `update(...)`, and `WorkflowDetail.template` SHALL behave identically
in async call paths. The sync/async duality rule requires this parity.

#### Scenario: AsyncWorkflowsClient.create() accepts template
- **WHEN** `await async_client.workflows.create(template={"key": "val"})` is called
- **THEN** the HTTP request body contains `"template": {"key": "val"}`
- **AND** the call does not raise a TypeError or AttributeError

#### Scenario: AsyncWorkflowsClient.update() accepts template
- **WHEN** `await async_client.workflows.update(id="wf-id", template={"key": "val"})` is called
- **THEN** the HTTP request body contains `"template": {"key": "val"}`
- **AND** the call does not raise a TypeError or AttributeError

### Requirement: Existing callers without template are unaffected (backward compatibility)
Existing callers that omit `template` SHALL continue to work without modification after
regen; the field is optional on both `WorkflowRequest` and `WorkflowDetail`. No existing
public method signature is changed; no existing field is removed or renamed.

#### Scenario: Existing create call without template succeeds after regen
- **WHEN** `client.workflows.create(name="my-workflow", steps=...)` is called with no `template`
- **THEN** the call succeeds and produces a valid `WorkflowResponse`
- **AND** `response.workflow.template` is `None` when the server returns no template

#### Scenario: Existing WorkflowDetail deserialization without template field succeeds
- **WHEN** a workflow API response body does not include `"template"` at all
- **THEN** `WorkflowDetail` deserialization succeeds
- **AND** `workflow_detail.template` is `None`

#### Scenario: WorkflowDetail with unknown additive fields still deserializes (tolerant reader)
- **WHEN** the API response includes a field not yet modeled in the current SDK version
- **THEN** `WorkflowDetail` deserialization succeeds (Pydantic `extra="allow"`)
- **AND** no exception is raised

### Requirement: README documents template usage for workflow create and update
`README.md` SHALL include at least one usage example demonstrating `template` in
`client.workflows.create(...)`. The example SHALL show a `dict[str, str]` value. The
README SHALL clarify that the field is optional and that the value is a string-to-string map.

#### Scenario: README contains a workflow create example with template
- **WHEN** a reader searches README.md for `template`
- **THEN** they find at least one `client.workflows.create(` call that includes `template={...}`
- **AND** the example value is a dict with string keys and string values

#### Scenario: README template example omits template to demonstrate optionality
- **WHEN** the README workflow section is read in its entirety
- **THEN** it conveys that omitting `template` is valid and leaves the field unset

### Requirement: CI quality gates pass after Fern regen
After regeneration, `poetry run mypy .` and `poetry run pytest -rP -n auto .` SHALL both
pass without errors or failures attributable to the `WorkflowTemplate` type or the
`template` field on `WorkflowRequest` / `WorkflowDetail`. `openspec/` being on
`.fernignore` SHALL ensure the change directory survives the regen.

#### Scenario: mypy passes on the regenerated SDK with WorkflowTemplate
- **WHEN** `poetry run mypy .` is executed on the repo after Fern regen
- **THEN** it exits with code 0
- **AND** no errors reference `WorkflowTemplate`, `WorkflowRequest.template`, or `WorkflowDetail.template`

#### Scenario: pytest passes on the regenerated SDK
- **WHEN** `poetry run pytest -rP -n auto .` is executed after Fern regen
- **THEN** it exits with code 0
- **AND** no failures reference `template` fields on workflow types

