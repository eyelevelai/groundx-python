# Design: Support Custom Workflow Steps

## Current Findings

### ADP POC

`/Users/benjaminfletcher/git/adp-poc/workflows/adp_401k_v1/prompt.yaml` has 11
top-level final sections. All 11 declare `slot: chunk-instruct`. The conversion
report records `workflow_load_exceptions.slot_field_counts["chunk-instruct"]`
as 159 fields and marks runtime prompt-load reduction as unresolved.

This means the ADP issue is not just bad slot assignment. The current workflow
model does not provide enough independent chunk-level output slots for a large
schema.

### Fern and Python SDK

`eyelevel-fern-config/fern/openapi.yml` defines `WorkflowSteps` as a fixed object
with named properties:

- `chunk-instruct`
- `chunk-keys`
- `chunk-summary`
- `doc-keys`
- `doc-summary`
- `search-query`
- `sect-instruct`
- `sect-keys`
- `sect-summary`

The generated Python SDK mirrors that in
`src/groundx/types/workflow_steps.py`. The Pydantic model allows extra fields,
but that is not enough for a supported feature because the public API schema,
Go runtime, X-Ray, docs, and Arcadia code do not define how those extra fields
are processed.

`WorkflowStepConfig.field` is a separate vocabulary from the step name. Current
allowed output fields are:

- `doc-sum`
- `doc-keys`
- `sect-sum`
- `sect-keys`
- `chunk-sum`
- `chunk-keys`
- `chunk-instruct`
- `text`

The existing distinction between step name and output field must stay explicit.

`eyelevel-fern-config/fern/generators.yml` also generates the TypeScript SDK
from the same OpenAPI contract. This feature is Python-centered, but Fern
schema changes must pass a TypeScript generation smoke check. TypeScript
feature documentation and examples may be deferred, but generator compatibility
cannot be treated as out of scope because the shared schema feeds both SDKs.

### cashbot-go

`cashbot-go/pkg/model/summarizer/process.go` already has:

- `Steps *map[StepType]map[molecule.Type]*Step`
- `Template *map[string]string`

`Template` is copied, overwritten, and passed into prompt rendering through
`process.Templates()`, but it is not exposed through Fern/OpenAPI/Python SDK
workflow config. The partner workflow create/update compatibility path also
does not copy top-level template config into `Process`, and the existing
`APIRequest.Template` field is a different partner template type. The locked
contract exposes public `template` as workflow/process config matching
`Process.Template *map[string]string`; it does not reuse the top-level partner
template object.

`StepType` is an enum in `pkg/model/summarizer/step_type.go`, so unknown custom
step names currently cannot be parsed into the main `Steps` map without a model
change.

`FieldType` is an enum in `pkg/model/summarizer/field_type.go`, so custom output
fields also need an explicit model. Otherwise several custom steps would still
collide into the same small set of output fields.

Output readback is currently fixed-field based:

- `chunk-keys` writes to `Chunk.MoleKeysD`/`Chunk.MoleKeys`, then X-Ray
  `chunkKeywords`
- `chunk-summary` writes molecule summary/search metadata, then X-Ray
  `suggestedText`
- `sect-summary` writes `Chunk.SectionMeta.Search`, then X-Ray
  `sectionSummary`
- `doc-summary` writes `Chunk.DocumentMeta.Search`, then X-Ray emits top-level
  `fileSummary` when one consistent document summary applies, or per-chunk
  `fileSummary` when chunk document summaries diverge

The Python SDK loader parses those fixed JSON fields, and Arcadia's routed
reassembly allowlist includes `chunkKeywords`, `sectionSummary`, and
chunk-level `fileSummary`. The Python document loader and Arcadia reassembly
currently iterate chunk fields and do not route top-level `xray.fileSummary` as
workflow output. The current runtime, SDK, Arcadia, and harness surfaces do not
have a generic custom output map. Custom step support therefore requires both a
storage decision and a readback/X-Ray decision, especially for document-level
outputs; adding step names alone is not enough.

### Arcadia

`internal-arcadia-agents/prompts/arcadia_manager.py` currently builds three
workflow steps:

- `chunk_instruct` for statement extraction
- `chunk_keys` for charge extraction
- `chunk_summary` for meter extraction

`internal-arcadia-agents/tasks/download.py` hardcodes the Celery graph as a
chord:

- `reconcile_meters -> qa_meters`
- `reconcile_statement -> qa_statement`
- body `save_agents -> agent -> save_agents`

`classes/arcadia_agent_request.py`, `tasks/agent.py`, and `tasks/save.py` are
tied to hardcoded request type strings and next-step routing.

Arcadia already depends on the SDK prompt manager to reload authored YAML from
the deployed workflow extract. Any custom step or task-graph contract must
therefore be preserved in the authored YAML path, not just in a local sidecar.
Its `Statement.load_xray` path currently reads only the fixed X-Ray output
fields listed in `XRAY_REASSEMBLY_OUTPUT_ATTRS`, so custom outputs must either
extend that allowlist or teach the reassembler the new custom output map shape.

### Harness and Docs

`groundx-studio-harness` currently documents and validates the old three-slot
menu in the extraction workflow skill. The compiler, X-Ray helper,
`templates/validate_workflow_json.py`, `SKILL.md`, `SKILL.public.md`,
`references/*`, `evals/evals.json`, examples, changelog entries, and scanner
tests all assume only the current proven slots. The local X-Ray helper reads
`chunkKeywords` for charges, `suggestedText`/`chunkSummary` for meters, and
`sectionSummary` for statement fields; it does not read custom output maps or
document `fileSummary`.

Public docs in `eyelevel-fern-config` currently teach the simple Python SDK
path with `prepare_extraction_yaml(...)`, workflow create, `client.ingest(...)`,
and `get_extract(...)`. Public docs should stay centered on the user-visible
workflow and should avoid harness terms.

## Locked Contract Direction

Use an explicit custom-step model instead of pretending arbitrary extra keys on
the existing `WorkflowSteps` object are enough.

The central planning contract is locked to this model:

- legacy fixed steps remain available as-is
- public workflow config adds a workflow-level `customSteps` array, separate
  from the legacy fixed `steps` object
- each custom step has a stable `name`
- each custom step declares a `level`: `chunk`, `section`, or `document`
- each custom step declares an extraction/output `kind`
- custom step names have one canonical form, explicit conversion rules between
  YAML, JSON, Go, Python, and X-Ray, and hard failures for invalid characters,
  duplicates, reserved names, fixed-step collisions, and duplicate output
  destinations
- each custom step has an exact public record shape: `name`, `level`, `kind`,
  optional `config`, and optional `requiredTemplateKeys`
- `config` reuses the existing element-targeted workflow step shape, but custom
  step config entries cannot set the legacy fixed-output `field`; custom output
  storage comes from `level`, `kind`, `outputRoutes`, and `leafFields`
- each custom step has an explicit output destination that can be stored,
  returned in X-Ray, and mapped back to extraction workflow groups
- the prepared metadata maps each workflow output back to its final JSON path,
  including the exact custom X-Ray/readback path used by Arcadia reassembly
- persisted workflow extract metadata has an explicit version and documented
  behavior for missing, current, unknown, and future versions
- `template` is exposed as workflow/process config matching Go
  `Process.Template *map[string]string`, and is shared by fixed and custom step
  prompts
- `template` is not exposed as a top-level partner compatibility field unless a
  repo-owned plan later proves that path is required and can keep the map type
  separate from the existing partner template object
- the contract enforces a maximum of 20 fields per executable workflow step in
  the public API/runtime path, derived or verified by the server from canonical
  `workflow.extract` metadata and mirrored by SDK, harness, and ADP validation

The public API field name is `customSteps`. It avoids changing the meaning of
the existing fixed `steps` field while keeping the API easy to explain.

The X-Ray/readback shape is one predictable map per level:
`customChunkOutputs`, `customSectionOutputs`, and `customDocumentOutputs`,
instead of generating many ad hoc top-level X-Ray fields. Fixed legacy outputs
such as `chunkKeywords`, `sectionSummary`, and `fileSummary` remain unchanged.
Custom document outputs are read from `customDocumentOutputs`, not from the
legacy top-level or per-chunk `fileSummary` behavior.

Custom outputs are persisted through explicit workflow custom-output metadata.
Repo-owned `cashbot-go` planning must first confirm whether the existing
`layout.CustomMeta` level model can carry the data; otherwise it must add
optional chunk/layout fields. Chunk-level custom outputs map to the Molecule
level, section-level custom outputs map to the Section level, and document-level
custom outputs map to the Document level. Missing custom-output metadata on old
documents is treated as empty. No backfill is required; if a storage backend
needs an added optional column or JSON field, repo-owned `cashbot-go` planning
must include the additive migration plus backward-compatible readers.

Document-level custom outputs must produce a single document value. They are
returned only through top-level `customDocumentOutputs`; they do not reuse the
legacy `fileSummary` behavior where a document summary can appear either
top-level or per chunk. If document-level custom output computation produces
conflicting per-chunk values, runtime validation fails instead of emitting a
divergent custom document result.

The release sequence is publish-last, then end-to-end validation. A spec PR may
define the shape and local generation is allowed before release for repo-level
verification. The final end-to-end path is expected to require published SDK and
docs artifacts, so publishing is the last prerequisite before e2e, not something
that waits until after e2e. The sequence is draft Fern/OpenAPI branch, local
Python and TypeScript generation or generator smoke output, SDK/runtime/harness
verification against the draft contract, runtime deployment verification,
published SDK and docs, e2e validation against the published artifacts, then
downstream dependency updates using lower bounds such as
`groundx-python >= <released version>`. If post-publish e2e fails, the release
is failed and must be fixed forward with a corrective patch or replacement
publication. Generated files in `groundx-python` must not be hand-edited or
committed as implementation work outside the approved Fern-generated release
path.

## YAML Authoring Direction

Extraction YAML should remain centered on the final JSON the application wants
back. Custom workflow steps should be authoring metadata, not final data groups.

Example high-level shape:

```yaml
workflow:
  metadata_version: 1
  template:
    plan_name: "ADP 401k plan"
  custom_steps:
    chunk:
      - name: adp_employer_information
        kind: instruct
        required_template_keys:
          - plan_name
      - name: adp_contribution_rules
        kind: instruct

employer_information:
  workflow_step: adp_employer_information
  fields:
    employer_name:
      workflow_output_key: employer_name
      prompt:
        description: Employer name.
        type: str
```

Representative custom step examples:

```yaml
workflow:
  metadata_version: 1
  custom_steps:
    chunk:
      - name: adp_employer_information
        kind: instruct
    section:
      - name: adp_contribution_rules
        kind: summary
    document:
      - name: adp_plan_overview
        kind: summary

employer_information:
  workflow_step: adp_employer_information
  fields:
    employer_name:
      workflow_output_key: employer_name
      prompt:
        description: Employer name.
        type: str

contribution_rules:
  workflow_step: adp_contribution_rules
  fields:
    employee_deferral_rule:
      workflow_output_key: employee_deferral_rule
      prompt:
        description: Employee deferral rule.
        type: str

plan_overview:
  workflow_step: adp_plan_overview
  fields:
    summary:
      workflow_output_key: summary
      prompt:
        description: Overall plan summary.
        type: str
```

Top-level `workflow:` is always reserved as authoring metadata. Since no known
legacy YAML uses `workflow` as a final output group, the SDK should fail clearly
if a YAML tries to use top-level `workflow:` as final data. Final YAML groups
assign to workflow steps with `workflow_step: <step-name>`.

Existing YAML that uses `slot:` remains supported for legacy fixed slots.
`workflow_step:` is the forward path for fixed and custom steps. If a group
declares both `slot` and `workflow_step`, preparation must fail clearly instead
of guessing precedence.

YAML-authored prompt template values live at workflow level as
`workflow.template`, matching public workflow/process `template` config and Go
`Process.Template *map[string]string`. Custom step entries may declare
`required_template_keys`, but they do not carry their own per-step `template`
maps.

Prompted fields may provide `workflow_output_key: <lower-snake-key>` as
authoring-only metadata beside `prompt:`. This is the only authored YAML location
for overriding the custom output map key. The SDK writes that value to persisted
route metadata as `output_key` and to public JSON `outputRoutes[]` records as
`outputKey`. `workflow_output_key` never appears in the final extracted JSON.

SDK YAML preparation derives `leaf_fields` from the final schema and workflow
assignments. Direct public workflow config uses a workflow-level `leafFields`
array when the caller bypasses YAML preparation. `leafFields` is the public
camelCase representation of persisted `workflow.extract.workflow.leaf_fields`.
Requests with custom workflow steps must provide or derive both `outputRoutes`
and `leafFields`; missing route or leaf metadata fails before execution.

The field-load rule hard-fails another ADP case where 159 fields are sent
through one executable step: one executable workflow step may own at most 20
fields. Harness and ADP validation must hard-fail when a step exceeds 20 fields,
but they cannot be the only guardrail. Direct SDK/API callers must be protected
by SDK preparation and public API/runtime validation.

The public API/runtime field-load source of truth is server-derived validation
over canonical persisted `workflow.extract.workflow.output_routes` and
`workflow.extract.workflow.leaf_fields`. SDK or harness preparation may include
per-executable-step field counts and an integrity record, but caller-provided
counts are not authoritative. The API/runtime must either recompute counts
directly from canonical workflow extract metadata or verify a
server-recomputable integrity record that binds the counts to the exact custom
step identities, `output_routes`, and `leaf_fields` being stored. Workflow
create/update requests that include custom extraction steps but omit verifiable
metadata, include stale, caller-only, or mismatched counts, carry an unknown
metadata version, or cannot be parsed into canonical field counts must fail
before execution.

## Remaining Contract Decisions

These decisions close the remaining Phase 0 blockers.

### Custom Step Records

Public `customSteps[]` records are exact. Each item contains:

- `name`: canonical lower-snake custom step name
- `level`: `chunk`, `section`, or `document`
- `kind`: one of the allowed output kinds for the level
- `config`: optional element-targeted workflow step config
- `requiredTemplateKeys`: optional string array

The initial level/kind matrix mirrors existing fixed workflow behavior:

- `chunk`: `instruct`, `keys`, `summary`
- `section`: `instruct`, `keys`, `summary`
- `document`: `keys`, `summary`

Invalid level/kind combinations fail validation. The persisted
`workflow.extract.workflow.custom_steps[]` form uses snake_case for
`required_template_keys`; the other logical fields remain `name`, `level`,
`kind`, and `config`.

`config` reuses the existing element-targeted workflow step shape with element
keys `all`, `figure`, `json`, `paragraph`, `table`, and `table-figure`. Each
element config may carry the existing prompt, engine, and include settings. It
must omit or null the legacy fixed-output `field`; custom output storage is
derived from the custom step record plus route and leaf metadata. If `config` is
omitted, repo-owned implementation plans must define the default prompt/config
behavior for that `level`/`kind`.

### Route Metadata

Persisted workflow metadata must include route records that map custom readback
outputs to final JSON fields. Authored YAML and persisted `workflow.extract`
metadata use snake_case keys; public workflow config and X-Ray JSON use camelCase
keys. Public workflow config exposes these records in a workflow-level
`outputRoutes` array. Persisted `workflow.extract.workflow` stores the same
records as `output_routes`.

Each route record must include:

- `workflow_group`: the prepared workflow group that owns the prompt field
- `workflow_field`: the prepared workflow field name
- `final_path`: the final JSON field as an RFC 6901 JSON Pointer
- `step_name`: the canonical custom step name
- `level`: `chunk`, `section`, or `document`
- `output_map`: one of `customChunkOutputs`, `customSectionOutputs`, or
  `customDocumentOutputs`
- `output_key`: the key used inside the custom output map
- `readback_path`: the exact X-Ray/readback path template

Authored YAML provides `output_key` through field-level `workflow_output_key`.
Direct public workflow config uses `outputKey` on `outputRoutes[]` records.
Persisted `workflow.extract` metadata uses snake_case `output_key`. These names
are the same logical value at different API boundaries.

Public `outputRoutes[]` records use camelCase keys: `workflowGroup`,
`workflowField`, `finalPath`, `stepName`, `level`, `outputMap`, `outputKey`, and
`readbackPath`. `level` must be one of `chunk`, `section`, or `document`.
`outputMap` must match `level`: `chunk` uses `customChunkOutputs`, `section`
uses `customSectionOutputs`, and `document` uses `customDocumentOutputs`.
`finalPath` must be an RFC 6901 JSON Pointer. Duplicate final paths and duplicate
`(outputMap, stepName, outputKey)` destinations fail. `readbackPath` stores the
canonical non-page path template for the output level; page-level chunk
companions are derived from the canonical route when X-Ray includes page chunks.

Route and leaf metadata must cross-check before hashing or execution. Every
custom `output_routes` record must have exactly one matching `leaf_fields` record
with the same `final_path`, `workflow_group`, `workflow_field`, `step_name`,
`level`, and `output_key`. Every `leaf_fields` record must have exactly one
matching `output_routes` record. The matched leaf record must also correspond to
a prompted final-schema leaf at `final_path`, with schema-derived `field_type`,
`is_repeated`, and `repetition_scope`. Missing, extra, duplicate, stale, or
mismatched route/leaf records fail before field-count hashing or execution.

Readback path templates are:

- chunk: canonical route `/chunks/*/customChunkOutputs/<step_name>/<output_key>`;
  page-level companion
  `/documentPages/*/chunks/*/customChunkOutputs/<step_name>/<output_key>`
- section: canonical route
  `/chunks/*/customSectionOutputs/<step_name>/<output_key>`; page-level
  companion
  `/documentPages/*/chunks/*/customSectionOutputs/<step_name>/<output_key>`
- document: `/customDocumentOutputs/<step_name>/<output_key>`

`final_path` and `readback_path` are intentionally different. `final_path` tells
Arcadia where the user wants the value in the final JSON. `readback_path` tells
SDK/Arcadia where the runtime returned the value.

### Naming And Normalization

Custom step names use lower snake case only:

```text
^[a-z][a-z0-9_]{0,63}$
```

Names with uppercase letters, hyphens, dots, spaces, leading underscores,
trailing underscores, or ambiguous auto-normalization are invalid. The canonical
identity is exactly the authored lower-snake-case string. There is no
case/kebab/camel conversion for custom step names.

Custom step names are globally unique across all custom levels, not merely
unique per level. They must not collide with fixed step names or their obvious
snake_case aliases, including `chunk_instruct`, `chunk_keys`, `chunk_summary`,
`sect_instruct`, `sect_keys`, `sect_summary`, `doc_keys`, `doc_summary`,
`search_query`, and `text`. They must also avoid reserved workflow/runtime keys:
`workflow`, `steps`, `custom_steps`, `customSteps`, `template`, `runtime`,
`output_routes`, `outputRoutes`, `leaf_fields`, `leafFields`, `field_counts`,
`fieldCounts`, `schema_hash`, `schemaHash`, `metadata_version`,
`metadataVersion`, `_defs`, `_pseudo_groups`, and
`_groundx_persisted_extract`.

`output_key` follows the same lower-snake-case rule. It defaults to the prepared
workflow field name when that name already satisfies the rule. If the prepared
workflow field name is nested or otherwise invalid for an output key, the SDK
must require an explicit valid field-level `workflow_output_key` in authored
YAML, or `outputKey` in direct public workflow config. Duplicate
`(output_map, step_name, output_key)` destinations fail. Duplicate final JSON
field routes also fail.

### Persisted Metadata Version

The reserved `workflow:` metadata block carries `metadata_version: 1` in
authored/persisted extract metadata. Public API JSON may expose the same concept
as `metadataVersion`, but `workflow.extract` remains the canonical validation
source.

Compatibility behavior:

- no `workflow:` block and no custom steps: legacy fixed-step fallback
- `workflow:` block with `metadata_version: 1`: load and validate current
  custom workflow metadata
- `workflow:` block with missing metadata version: fail if custom steps,
  output routes, or custom output maps are present
- unknown, future, non-integer, or unsupported metadata versions: fail closed
- current-version metadata must never be silently dropped during reload

### Field-Count Validation

The 20-field limit counts distinct final leaf field routes assigned to one
executable workflow step. Repeated/list field definitions count as one field
definition at schema validation time unless they introduce separate prompted
leaf fields.

The server recomputes counts from canonical
`workflow.extract.workflow.output_routes` and
`workflow.extract.workflow.leaf_fields`. SDK/harness may include `field_counts`
and a `schema_hash` as a convenience, but the server treats those as
non-authoritative hints. If hints are present, they must match the server
recomputed counts and canonical hash. If custom steps are present but the server
cannot recompute counts from canonical route and leaf-field metadata, workflow
create/update fails.

The canonical hash is SHA-256 over sorted-key, no-whitespace canonical JSON
using persisted snake_case keys. Arrays are sorted before hashing with these
ascending lexicographic identity tuples:

- `custom_steps`: `(name)`
- `output_routes`: `(final_path, workflow_group, workflow_field, step_name,
  output_key)`
- `leaf_fields`: `(final_path, workflow_group, workflow_field, step_name,
  output_key)`

The hash input is exactly:

- `metadata_version`
- `custom_steps`: one record per custom step with `name`, `level`, `kind`, and
  any declared `required_template_keys`
- `output_routes`: the route records described above
- `leaf_fields`: one record per prompted final leaf field with `final_path`,
  `workflow_group`, `workflow_field`, `step_name`, `level`, `output_key`,
  `field_type`, `is_repeated`, and `repetition_scope`

`leaf_fields` records use persisted snake_case keys. Public direct config uses
the camelCase `leafFields[]` equivalent: `finalPath`, `workflowGroup`,
`workflowField`, `stepName`, `level`, `outputKey`, `fieldType`, `isRepeated`,
and `repetitionScope`. `is_repeated` is a boolean. `repetition_scope` is one of
`none`, `field`, or `item`: `none` is valid only when `is_repeated` is false;
`field` means a repeated/list value is prompted as one leaf and counts as one
field for the step; `item` means repeated item/object schema introduces separate
prompted leaves, and each prompted item leaf must appear as its own `leaf_fields`
record at its full schema-level `final_path`. Invalid combinations fail before
hashing or execution.

For `repetition_scope: item`, the canonical `final_path` uses a literal `*`
segment at each repeated-item boundary, such as `/fees/*/amount`. The `*`
segment is a schema wildcard, not a runtime array index. It is still encoded as
an RFC 6901 path segment and is reserved by this contract for repeated item
schemas. Counts use the wildcard schema path once per prompted item leaf, not
once per runtime array element. Duplicate wildcard final paths fail the same way
as duplicate non-repeated final paths.

Prompt prose, examples, model parameters, template values, and other data that
does not affect executable-step field load are excluded from the field-count
hash. Caller-only counts or hashes without matching canonical metadata are
rejected.

### Template Validation

`template` is a workflow/process-level `map[string]string`. Public config keys
are supplied without `{{...}}`; the runtime may accept already-braced keys for
compatibility but stores and compares normalized logical keys. Values are literal
strings. Template values are not recursively rendered or executed.

Template validation rules:

- template must be a map of string keys to string values
- keys must match `^[A-Za-z][A-Za-z0-9_]{0,63}$` after removing optional
  surrounding braces
- keys using the reserved `GROUNDX_` prefix or workflow metadata names are
  rejected
- documented system prompt keys such as `LANGUAGE` and `PAGE_NUMBERS_*` may be
  overridden because cashbot-go already supports default override behavior
- extra keys are allowed because the template bag can serve multiple prompts
- required template keys are declared explicitly on a workflow step as
  `required_template_keys` in persisted/YAML metadata and `requiredTemplateKeys`
  in public JSON; missing declared keys fail before rendering
- required template keys use the same brace normalization, key regex, reserved
  prefix, and workflow-metadata reserved-name checks as `template` keys; duplicate
  required keys after normalization fail validation
- unresolved optional placeholders keep the existing renderer behavior for
  legacy fixed prompts
- total serialized template payload must be no larger than 16 KiB, and one value
  must be no larger than 4 KiB
- invalid template shape fails workflow create/update; render-time failures
  fail the workflow step with a clear step/template error

Reserved workflow metadata template keys are checked after brace normalization.
The reserved set is: `workflow`, `steps`, `custom_steps`, `customSteps`,
`template`, `runtime`, `output_routes`, `outputRoutes`, `leaf_fields`,
`leafFields`, `field_counts`, `fieldCounts`, `schema_hash`, `schemaHash`,
`metadata_version`, `metadataVersion`, `workflow_group`, `workflowGroup`,
`workflow_field`, `workflowField`, `final_path`, `finalPath`, `step_name`,
`stepName`, `output_key`, `outputKey`, `readback_path`, `readbackPath`, `_defs`,
`_pseudo_groups`, and `_groundx_persisted_extract`.

### TypeScript Smoke Gate

The shared Fern schema must pass TypeScript generation even if TypeScript
feature docs are deferred. The repo-owned Fern plan must run
`fern generate --group ts-sdk`, and must record evidence that the generator
accepts `customSteps`,
custom step `config`, custom step legacy `field` rejection, `outputRoutes`,
`outputKey`, `leafFields`, route/leaf matching fields, `isRepeated`,
`repetitionScope`, wildcard repeated-item final paths, `template`,
`requiredTemplateKeys`, reserved template key validation, the custom output map
schemas, and the 20-field validation/metadata schema without generator errors. A
TypeScript generation failure blocks the shared OpenAPI/Fern contract change.

## Arcadia Runtime Direction

Arcadia should not execute arbitrary YAML. It should support an allowlisted
runtime graph definition where YAML can select and order known task types.

Follow-on concept:

```yaml
runtime:
  graph:
    - id: reconcile_statement
      task: reconcile_statement
      after: download
    - id: qa_statement
      task: qa_statement
      after: reconcile_statement
```

When this block is missing, Arcadia must run the current hardcoded production
graph exactly as it does today.

The follow-on Arcadia fields plan must choose and document whether this belongs
under a generic `runtime`, `orchestration`, or workflow-specific metadata key.
Any implementation must validate:

- only known tasks are allowed
- graph references are acyclic
- required save/finalization stages exist
- existing request types remain supported
- missing routed required values keep current hard-error behavior where already
  defined
- each authorable task has a documented input payload, output payload, retry or
  idempotency assumption, and failure propagation behavior
- chord/chain failures preserve current production error handling or fail with a
  reviewed, explicit replacement behavior

For the current plan, Arcadia keeps the existing reconcile, QA, and save task
families except `qa_charges`, which is classified as dead legacy. The supported
existing business actions remain `reconcile_charges`, `reconcile_meters`,
`reconcile_statement`, `qa_meters`, `qa_statement`, `save_charges`,
`save_meters`, and `save_statement`. The current `agent` and `save_agents` nodes
stay internal and are preserved by a default compatibility adapter when custom
runtime metadata is absent.

A follow-on plan, created after cleanup and closeout of this central plan, must
define and implement three new custom Arcadia actions:
`reconcile_fields`, `qa_fields`, and `save_fields`. That follow-on plan must
define what each action does, its input payload, output payload, retry or
idempotency assumptions, failure propagation behavior, and required updates in
`internal-arcadia-agents`. This central plan may record an
`internal-arcadia-agents` deferral stub, but it must not require or start the
follow-on Arcadia fields implementation before the central cleanup/closeout gate.

## Template Direction

Expose the existing Go `Process.Template *map[string]string` setting through
public workflow/process config and generated SDKs. This follows the cashbot-go
runtime path where `Process.Template` is loaded into prompt rendering through
`gpt.InitTemplates(...)`. It must not be confused with the separate partner
request template object. This must include:

- Fern/OpenAPI schema update
- generated Python SDK access
- Go request/response/load/save tests
- prompt rendering tests proving template values reach prompt expansion
- validation tests for unknown keys, missing required keys, reserved keys,
  invalid value types, excessive payload size, escaping/rendering failures, and
  fixed/custom prompt behavior
- docs and harness guidance
- release notes or version gates so downstream repos depend on
  `groundx-python >= <released version>` instead of an exact pin

## Compatibility

Legacy behavior is required:

- existing YAML with `slot:` continues to work
- new YAML uses `workflow_step:` for fixed and custom step assignment
- existing `WorkflowSteps` fixed fields continue to work
- workflows without custom steps run the default pipeline as before
- Arcadia runs the existing chord/chain when no runtime graph metadata is
  present
- `qa_charges` is treated as dead legacy, not an authorable runtime task
- old ADP/Arcadia YAML can be prepared and loaded without custom steps
- existing tests are not weakened unless the user explicitly approves or a
  review proves the test no longer represents correct behavior
- public docs are updated only after runtime, SDK, and harness behavior are
  verified
- TypeScript generation compatibility is verified for shared Fern schema changes
  even if TypeScript feature guidance is deferred
- generated SDK and docs publishing happens only after local/runtime/schema/SDK
  and harness verification, and immediately before the final e2e path that
  requires published artifacts
- downstream dependency updates are blocked until the published-artifact e2e
  path passes
- implementation does not begin until the post-contract repo-specific plans
  exist with exact failing tests, expected failures, implementation steps,
  verification commands, and commit checkpoints
- implementation does not begin in a target repo until a clean isolated branch or
  worktree exists and unrelated local changes are recorded as out of scope

## Archive Ownership

This central OpenSpec change is planning-only and cross-repo. It must not be
archived into `groundx-python` specs while it contains durable requirements owned
by `cashbot-go`, `eyelevel-fern-config`, `internal-arcadia-agents`,
`groundx-studio-harness`, or `adp-poc`. Before archive, repo-owned OpenSpec
changes must absorb their durable spec deltas. The central change can then be
closed as planning documentation or reduced to requirements owned by
`groundx-python` only.

## Alternatives Considered

### Approach A: Add Arbitrary Keys To `WorkflowSteps`

This is tempting because the Python generated model allows extra keys. It is
not sufficient. Go currently parses step keys into `StepType`, X-Ray has fixed
fields, and docs/scanners do not know what extra keys mean. This approach hides
the hard work.

### Approach B: Add More Fixed Enum Slots

This might solve ADP briefly but repeats the current limit. It does not create
a real customer-defined model for chunk, section, and document steps.

### Approach C: Add Explicit Custom Step Arrays

This is the recommended direction. It preserves legacy fixed steps, gives the
runtime a typed place for custom step definitions, and allows X-Ray/Arcadia/docs
to reason about named custom outputs.

## Risks

- Custom step names may be confused with output field names unless the API keeps
  those concepts separate.
- X-Ray output may become hard to consume if custom fields are emitted as many
  top-level ad hoc keys instead of a predictable map.
- Chunk-only tracing could produce a design that fails for section or document
  outputs.
- A reserved `workflow:` YAML section could accidentally steal a legacy final
  group named `workflow`.
- A YAML that tries to use top-level `workflow:` as final output data must fail
  clearly now that `workflow:` is always reserved.
- Custom X-Ray output could be readable but still unusable by Arcadia if route
  metadata does not include the exact custom output path.
- Caller-provided field-count metadata could be spoofed unless the API/runtime
  derives or verifies counts from canonical workflow extract metadata.
- OpenAPI changes could break TypeScript generation even if the Python SDK path
  works.
- Arcadia could become unsafe if YAML can name arbitrary Celery tasks or import
  arbitrary functions.
- Harness docs and public docs can drift if both are not updated after the SDK
  and runtime behavior is real.
- A design that only works for ADP could break invoice/utility extraction.

## Required Discovery Before Implementation

The first task is not code. It is a full trace of `chunk-keywords` from public
workflow config through Go processing, chunk storage, X-Ray output, SDK parsing,
harness aggregation, and Arcadia reassembly, plus representative section and
document summary traces through the same surfaces. The final implementation
plan must be updated after that trace. After the public contract is locked, the
next step is to create repo-specific implementation plans before code changes.
