# Design: Extraction Workflow Definition Methods

## Selected Approach

Add a hand-written, high-level extraction definition layer in the Python SDK:

- `GroundX.load_extraction_definition(...)`
- `GroundX.load_extraction_definition_from_yaml(...)`
- `GroundX.load_extraction_definition_from_workflow(...)`
- `GroundX.create_extraction_workflow(...)`
- `GroundX.update_extraction_workflow(...)`
- async parity on `AsyncGroundX`

The consolidated load method returns an SDK-owned `ExtractionDefinition` object
from exactly one source. The source-specific load methods remain available as
explicit aliases. The create and update methods accept either an
`ExtractionDefinition` or a YAML source, then delegate to the existing generated
workflow create/update clients.

The generated Fern workflow client remains available for direct low-level use.
`prepare_extraction_yaml(...)`, `load_from_yaml(...)`, `load_from_mapping(...)`,
and mapping-to-`Group` helpers remain available as advanced building blocks, but
they are not the promoted path for humans, public docs, harnesses, or
`internal-arcadia-agents`.

## Public SDK Shape

Promoted path from YAML:

```python
workflow = client.create_extraction_workflow(
    path="statement.yaml",
    name="statement extraction",
)

updated = client.update_extraction_workflow(
    "workflow-id",
    path="statement.yaml",
    name="statement extraction",
)
```

Promoted reusable definition path:

```python
definition = client.load_extraction_definition(path="statement.yaml")
existing = client.load_extraction_definition(workflow_id="workflow-id")
```

Explicit alias paths for callers who want source-specific method names:

```python
definition = client.load_extraction_definition_from_yaml(path="statement.yaml")
existing = client.load_extraction_definition_from_workflow("workflow-id")
```

The common YAML source is `path=...`, and public docs should show it directly
on create/update for the one-shot create or update workflow. Callers use
`ExtractionDefinition` when they need to inspect, reuse, or copy workflow
settings, especially from an existing workflow ID. Advanced and test callers may
pass `yaml_text`, `mapping`, or `prepared` explicitly. Create/update callers may pass
exactly one of:

- `definition`: an existing `ExtractionDefinition`.
- `path`: local filesystem path to read as UTF-8 YAML.
- `yaml_text`: raw YAML text.
- `mapping`: an authored YAML-shaped mapping by default. Advanced callers may
  pass an existing workflow `extract` mapping only with
  `mapping_kind="workflow_extract"`. Persisted/execution `extract` mappings may
  load with `prepared=None` when authored YAML metadata is unavailable.
- `prepared`: an existing `PreparedExtractionYaml`.

Exactly one source is required for create/update and for the consolidated
loader. The SDK does not silently prefer one source over another; zero or
multiple sources raise `ValueError`. This avoids ambiguous behavior where a
string might be either raw YAML text or a filesystem path.

## Definition Contract

`ExtractionDefinition` is the high-level object humans and agents should hold
when they need to inspect, reuse, create, or update extraction workflow
configuration.

Suggested shape:

```python
@dataclass(frozen=True)
class ExtractionDefinition:
    extract: Mapping[str, Any]
    prepared: PreparedExtractionYaml | None = None
    template: Mapping[str, str] | None = None
    custom_steps: Sequence[Mapping[str, Any]] | None = None
    output_routes: Sequence[Mapping[str, Any]] | None = None
    leaf_fields: Sequence[Mapping[str, Any]] | None = None
    chunk_strategy: Any | None = None
    section_strategy: Any | None = None
    steps: Any | None = None
```

The final implementation may add small convenience properties if tests prove
they are needed. The normal definition-loading path should not expose generated
Fern classes.

`ExtractionDefinition` normalizes generated workflow response models into plain
Python data suitable for the generated workflow client. In particular,
`template` is a string-to-string mapping. Non-string template values are invalid
for this helper and should raise a clear `ValueError` rather than being coerced
silently. Placeholder-style keys such as `{{LANGUAGE}}` and
`{{LANGUAGE_UNKNOWN}}` are plain string keys and must be preserved exactly,
including an empty string value for `{{LANGUAGE_UNKNOWN}}` when supplied.

`load_extraction_definition(...)` is the promoted loader. It accepts exactly one
of `workflow_id`, `path`, `yaml_text`, `mapping`, or `prepared`. It dispatches to
the same source-specific behavior as the explicit alias methods and fails rather
than choosing precedence when multiple sources are supplied.

`load_extraction_definition_from_yaml(...)` prepares authored YAML through the
existing `prepare_extraction_yaml(...)` path, then wraps the prepared result in
`ExtractionDefinition`. YAML-loaded definitions always have `prepared`.
When `mapping_kind` is omitted or set to `"authored_yaml"`, `mapping` follows
the same preparation path as `yaml_text`. When `mapping_kind` is
`"workflow_extract"`, the loader treats `mapping` as an existing workflow
`extract` payload, preserves it directly, and only sets `prepared` if the
persisted extract can be round-tripped through `prepare_extraction_yaml(...)`.
This explicit selector is required because a simple authored YAML mapping and a
simple execution-only workflow extract mapping can both be dictionaries whose
top-level keys are group names.

`load_extraction_definition_from_workflow(workflow_id)` calls the generated
workflow read/get API with the workflow ID, extracts the workflow's `extract`
mapping and workflow-level extraction settings, then returns the same
`ExtractionDefinition` shape. Top-level workflow response fields
(`template`, `custom_steps`, `output_routes`, `leaf_fields`, `chunk_strategy`,
`section_strategy`, and `steps`) are authoritative when present. When those
fields are absent, the loader may fall back to persisted metadata under
`extract["workflow"]`.

Workflow-loaded definitions only have `prepared` when the persisted extract can
be round-tripped through `prepare_extraction_yaml(...)`, usually because
`_groundx_persisted_extract` is present. If the workflow only contains execution
groups and workflow-level settings, return `prepared=None` instead of inventing
authored metadata. If the workflow does not contain an extraction `extract`
mapping, raise a clear exception naming the workflow ID.

## Workflow Kwargs Assembly

Create/update methods consume `ExtractionDefinition` and internally build the
same workflow settings callers currently write by hand:

- `extract` is `definition.extract`.
- `template` is copied from `definition.template` when present, after verifying
  all template values are strings.
- `custom_steps` is copied from `definition.custom_steps` when present.
- `output_routes` is copied from `definition.output_routes` when present.
- `leaf_fields` is copied from `definition.leaf_fields` when present.
- `name` is included when supplied.
- `chunk_strategy` defaults to `"element"` for extraction workflow helpers and
  can be set to `None` to omit it. Workflow-loaded definitions may preserve
  `definition.chunk_strategy` when the caller does not override it.
- `section_strategy` is included only when supplied or preserved from a
  workflow-loaded definition.
- `steps` is included when supplied or preserved from a workflow-loaded
  definition.

When custom workflow steps are present and `steps` is not supplied, the
create/update path must include an empty fixed-step overlay so YAML-authored
custom steps do not accidentally run alongside fixed default steps. The overlay
is a `WorkflowSteps` value with every known fixed stage set explicitly to
`None`: `chunk_instruct`, `chunk_keys`, `chunk_summary`, `doc_keys`,
`doc_summary`, `sect_instruct`, and `sect_summary`. Serialized requests must
carry those disabled fixed-step keys in the generated wire shape. Legacy YAML
without custom workflow steps should not receive that overlay unless the caller
supplies `steps`.

The kwargs assembly may live in a private helper, for example
`_workflow_kwargs_from_extraction_definition(...)`. It should not be promoted in
public docs.

## Optional Extract Dependency Boundary

The exported `GroundX` and `AsyncGroundX` clients live in `src/groundx/ingest.py`,
which is part of the base SDK import path. That file must not import
`groundx.extract` or optional extract dependencies at module import time. Instead,
the extraction definition methods lazy-import the extract workflow module inside
the method body. If the user installed only `groundx` and calls an extraction
definition method, raise an actionable error that says to install
`groundx[extract]`.

Tests must prove:

- `import groundx` and `from groundx import GroundX, AsyncGroundX` still work in
  an environment without extract optional dependencies;
- non-extraction client methods remain usable without extract extras;
- base SDK import does not import `groundx.extract` or representative
  `groundx[extract]` optional dependencies such as `yaml`, `boto3`, `PIL`,
  `google`, `gspread`, `minio`, `redis`, `celery`, `fastapi`, `openai`, or
  `smolagents`;
- calling extraction definition methods without extract extras fails with the
  install hint rather than an unrelated import traceback.

New hand-written tests under `tests/custom` must also respect the SDK
regeneration boundary. Before adding another `tests/custom/...` file, update or
verify `.fernignore` protects that hand-written test surface so the file is not
lost on the next Fern SDK release.

## Client Methods

`GroundX.load_extraction_definition(...)` loads an `ExtractionDefinition` from
exactly one source: `workflow_id`, `path`, `yaml_text`, `mapping`, or
`prepared`. `workflow_id` uses the workflow loader behavior; the other sources
use the YAML/prepared loader behavior. Passing zero or multiple sources raises a
clear `ValueError` instead of applying precedence.

`GroundX.load_extraction_definition_from_yaml(...)` loads authored YAML into
`ExtractionDefinition`. It remains available as an explicit alias for YAML,
mapping, and prepared-object sources.

`GroundX.load_extraction_definition_from_workflow(id, ...)` fetches an existing
workflow and converts its persisted extraction config into
`ExtractionDefinition`. It remains available as an explicit alias for workflow
ID sources.

`GroundX.create_extraction_workflow(...)` resolves exactly one source into an
`ExtractionDefinition`, assembles generated workflow kwargs internally, and
forwards them to `self.workflows.create(...)`.

`GroundX.update_extraction_workflow(id, ...)` resolves exactly one source into
an `ExtractionDefinition`, assembles generated workflow kwargs internally, and
forwards them to `self.workflows.update(id, ...)`.

Sync and async loader/create/update paths should use the same source-selection
helper so `workflow_id`, `definition`, `path`, `yaml_text`, `mapping`,
`mapping_kind`, and `prepared` validation cannot drift. `mapping_kind` is valid
only when `mapping` is the selected source. `request_options` is valid only
when the selected loader source is `workflow_id`.

Create/update methods return the normal generated `WorkflowResponse`. They do
not return `PreparedExtractionYaml`; callers who need metadata inspection use
the definition object. Callers who specifically need authored YAML preparation
metadata use `definition.prepared` when it is present or the lower-level
`prepare_extraction_yaml(...)` API when they have authored YAML.

Update is a full workflow settings overlay, not a patch. The docs must state
that callers should pass the YAML or definition again when updating so custom
workflow settings are not reset by a name-only update.

## Documentation Contract

The promoted extraction definition and workflow methods are hand-written SDK
convenience methods like `ingest` and `ingest_directories`. They must be
documented with the same level of prominence:

- SDK method docstrings in `src/groundx/ingest.py` with parameters, return
  values, sync examples, async examples where relevant, update semantics, and
  explicit bucket/account assignment follow-up.
- Public Fern docs with method-level reference sections for
  `client.load_extraction_definition(...)`,
  `client.load_extraction_definition_from_yaml(...)`,
  `client.load_extraction_definition_from_workflow(...)`,
  `client.create_extraction_workflow(...)`, and
  `client.update_extraction_workflow(...)`.
- Harness and plugin references that list these methods as hand-maintained
  Python SDK helpers beside `ingest` and `ingest_directories`.
- Harness public extraction-doc guidance, especially
  `skills/groundx-extraction-workflows/references/public-docs.md`, must be
  updated from the old `prepare_extraction_yaml(...)` primary flow to the new
  helper-backed public flow. The primary create/update examples should pass the
  YAML path directly to `client.create_extraction_workflow(...)` and
  `client.update_extraction_workflow(...)`; definition-loading examples should
  be framed as inspection, reuse, or copy-from-existing-workflow operations.
  Public prose should stay customer-readable; method names may appear in
  signatures and code examples, but explanatory copy should prefer "YAML",
  "workflow settings", and "JSON you want back" over internal jargon when
  possible.
- Extraction workflow guides that continue to show
  `client.workflows.add_to_id(...)` or `client.workflows.add_to_account(...)`
  after workflow creation because assignment is intentionally not implicit.
- Harness source-of-truth updates that include the owning skill references,
  evals, scanner expectations, routing/source manifests if behavior or
  discoverability changes, generated plugin mirrors, and version/changelog
  surfaces when required by the harness repo.
- Web UI or scaffold docs touched by this work must preserve the product UI
  invariant: the base experience is an authenticated app shell, and onboarding
  is a configurable overlay/app metadata flow for first-session guidance.

Advanced docs may mention `prepare_extraction_yaml(...)`, `load_from_yaml(...)`,
and `load_from_mapping(...)`, but primary examples should not teach them as the
normal workflow-management path.

## Error Handling

- Missing source: raise `ValueError` naming the accepted source arguments.
- Multiple sources: raise `ValueError` naming the conflicting arguments.
- `mapping_kind` supplied without `mapping` as the selected source: raise
  `ValueError`.
- Missing file path: raise `FileNotFoundError`.
- Workflow ID not found: surface the generated API error.
- Workflow exists but lacks extraction config: raise a clear error naming the
  workflow ID.
- Workflow exists but lacks authored metadata: return an `ExtractionDefinition`
  with `prepared=None` when create/update can still preserve the workflow
  payload, and document that authored metadata inspection is unavailable.
- Invalid YAML, custom-step metadata, route/leaf mismatch, field-count overload,
  or template errors: surface the existing `prepare_extraction_yaml(...)` error.
- Template mappings with non-string values: raise `ValueError` naming the
  offending template key.
- Missing `name` on create: raise `ValueError`.
- Omitted `name` on update: allowed; update should send the full extraction
  settings and omit only the name.

## Fern/OpenAPI Boundary

This change does not rename generated OpenAPI schemas or generated SDK classes.
The existing generated names remain part of the low-level workflow API. The new
definition methods reduce normal user exposure to those names without changing
the server contract.

If schema naming cleanup is still desired, create a separate OpenSpec plan that
weighs generated SDK import churn, TypeScript generation, docs updates, and
backward compatibility.

## Repo Impact

`groundx-python` owns the new SDK methods, `ExtractionDefinition`, tests,
exports, docstrings, and README or reference documentation for the new
hand-written methods.

`eyelevel-fern-config` updates public docs to replace the manual
`prepare_extraction_yaml(...)` plus metadata-copying snippet with
`client.create_extraction_workflow(path=..., name=...)`, an update example,
`client.load_extraction_definition(...)` docs for YAML and workflow-ID sources,
explicit alias docs, and method-level documentation matching the existing
hand-written SDK helpers.

`groundx-studio-harness` updates runtime/deploy templates to prefer the helper
methods when installed, keeps `workflow_sdk_kwargs(...)` for offline compile
output and older SDK fallback, and updates scanners/tests/docs including
architecture and SDK-surface references that currently list `ingest` and
`ingest_directories`.

`internal-arcadia-agents` evaluates adopting the definition methods for
load/create/update calls. If the methods can preserve Arcadia's specialized
metadata-key sets and custom workflow steps, use them. If not, keep the existing
explicit calls and record why.

`adp-poc` is scanned for manual workflow create/update snippets and updated only
where it owns executable docs or scripts. The scan found no owned boilerplate to
update; the prior whitespace-only local change was removed and the worktree is
clean.
