# Fixed Output Trace

This trace is the anchor for the custom step plan. `chunk-keys` is the closest
current analogue for a custom chunk-level output, but the final design must also
cover representative section-level and document-level outputs.

## Chunk-Level Name Changes

| Layer | Name |
| --- | --- |
| Workflow step key | `chunk-keys` |
| Python SDK `WorkflowSteps` attr | `chunk_keys` |
| Python SDK `WorkflowStepConfig.field` value | `chunk-keys` |
| Go step enum | `summarizer.ChunkKeys` |
| Go field enum | `summarizer.ChunkKeysF` |
| Go chunk storage | `layout.Chunk.MoleKeysD` / `layout.Chunk.MoleKeys` |
| Go setter | `layout.Chunk.SetChunkKeys(...)` |
| Go X-Ray field | `chunkKeywords` |
| Python extract X-Ray model | `Chunk.chunkKeywords` |
| Python document loader | parses `chunk.chunkKeywords` as JSON |
| Harness X-Ray helper | reads `chunk["chunkKeywords"]` |
| Arcadia runtime metadata tests | include `chunkKeywords` as a readable X-Ray field |

## Section-Level Name Changes

| Layer | Name |
| --- | --- |
| Workflow step key | `sect-summary` |
| Python SDK `WorkflowSteps` attr | `sect_summary` |
| Python SDK `WorkflowStepConfig.field` value | `sect-sum` |
| Go step enum | `summarizer.SectSummary` |
| Go field enum | `summarizer.SectSumF` |
| Go storage | `layout.Chunk.SectionMeta.Search` |
| Go setter/getter | `layout.Chunk.SetSectionSummary(...)` / `GetSectionSummary()` |
| Go X-Ray field | `sectionSummary` |
| Python extract X-Ray model | `Chunk.sectionSummary` |
| Python document loader | parses `chunk.sectionSummary` as JSON |
| Harness X-Ray helper | reads `sectionSummary` for statement scalar fields |
| Arcadia runtime metadata | `XRAY_REASSEMBLY_OUTPUT_ATTRS` includes `sectionSummary` |

## Document-Level Name Changes

| Layer | Name |
| --- | --- |
| Workflow step key | `doc-summary` |
| Python SDK `WorkflowSteps` attr | `doc_summary` |
| Python SDK `WorkflowStepConfig.field` value | `doc-sum` |
| Go step enum | `summarizer.DocSummary` |
| Go field enum | `summarizer.DocSumF` |
| Go storage | `layout.Chunk.DocumentMeta.Search` |
| Go setter/getter | `layout.Chunk.SetDocumentSummary(...)` / `GetDocumentSummary()` |
| Go X-Ray field | top-level JSON `fileSummary` (`XRay.Summary`) when one document summary applies; per-chunk JSON `fileSummary` (`XRayChunk.FileSummary`) only when chunk summaries diverge |
| Python extract X-Ray model | `XRayDocument.fileSummary` and `Chunk.fileSummary` |
| Python document loader | currently parses `Chunk.fileSummary` as JSON but does not parse top-level `XRayDocument.fileSummary` |
| Harness X-Ray helper | does not currently aggregate `fileSummary` |
| Arcadia runtime metadata | `XRAY_REASSEMBLY_OUTPUT_ATTRS` includes chunk-level `fileSummary`; `Statement.load_xray` iterates chunks, not top-level X-Ray metadata |

## Current Code Points

### eyelevel-fern-config

- `fern/openapi.yml` defines `WorkflowStepConfig.field` enum values, including
  `chunk-keys`.
- `fern/openapi.yml` defines fixed `WorkflowSteps` properties, including
  `chunk-keys`.
- `fern/openapi.yml` defines `WorkflowSteps` properties for `sect-summary` and
  `doc-summary`, and `WorkflowStepConfig.field` enum values for `sect-sum` and
  `doc-sum`.
- `fern/openapi.yml` exposes `WorkflowRequest`/`WorkflowDetail` fields for
  `chunkStrategy`, `name`, `extract`, `sectionStrategy`, and `steps`; it does
  not expose `template`.
- `fern/generators.yml` generates both Python and TypeScript SDKs from the
  shared OpenAPI contract.

### groundx-python

- `src/groundx/types/workflow_steps.py` exposes `chunk_keys`.
- `src/groundx/types/workflow_step_config_field.py` includes literal
  `chunk-keys`, `sect-sum`, and `doc-sum`.
- `src/groundx/extract/classes/groundx.py` has fixed X-Ray fields
  `chunkKeywords`, `fileKeywords`, `fileSummary`, `sectionKeywords`,
  `sectionSummary`, and `suggestedText`; it has no generic custom output map.
- `src/groundx/extract/classes/document.py` parses `chunk.sectionSummary`,
  `chunk.suggestedText`, `chunk.chunkKeywords`, `chunk.sectionKeywords`,
  `chunk.fileKeywords`, and `chunk.fileSummary` as JSON.
- `src/groundx/extract/classes/document.py` does not currently parse
  `XRayDocument.fileSummary`, even though `XRayDocument` has that field.
- `src/groundx/extract/prompt/utility.py` currently reserves `_defs`,
  `_pseudo_groups`, and `_groundx_persisted_extract`; it does not treat
  top-level `workflow:` as a special authoring section.
- `src/groundx/extract/prompt/manager.py` persists workflow route metadata
  through `workflow_field_paths`, `persisted_workflow_extract`, and related
  metadata accessors.
- `tests/extract/classes/test_groundx.py` asserts `chunkKeywords` is parsed.
- The SDK X-Ray/readback trace must be expanded to include custom section and
  document output maps after the public output shape is chosen.
- The SDK YAML trace must include reserved top-level authoring keys and legacy
  final groups named `workflow`.

### cashbot-go

- `pkg/model/summarizer/step_type.go` maps `chunk-keys` to `ChunkKeys`.
- `pkg/model/summarizer/step_type.go` accepts only fixed step names in
  `UnmarshalText`, so arbitrary custom step names cannot enter the current
  `Steps` map.
- `pkg/model/summarizer/field_type.go` maps `chunk-keys` to `ChunkKeysF`.
- `pkg/model/summarizer/field_type.go` accepts only fixed field names in
  `UnmarshalText`, so custom output fields need a separate model or expanded
  validation contract.
- `pkg/model/summarizer/process.go` maps `ChunkKeys` to `ChunkKeysF`.
- `pkg/model/summarizer/process.go` maps `SectSummary` to `SectSumF` and
  `DocSummary` to `DocSumF`.
- `pkg/model/summarizer/process.go` writes `ChunkKeysF` through
  `cnk.SetChunkKeys(...)`.
- `pkg/model/summarizer/process.go` writes `SectSumF` through
  `cnk.SetSectionSummary(...)` and `DocSumF` through
  `cnk.SetDocumentSummary(...)`.
- `pkg/model/summarizer/process.go` already carries
  `Template *map[string]string`, and `Process.Copy()` preserves it.
- `pkg/processor/summarizer/chunks.go` runs `Summarizer.ChunkKeywords(...)`.
- `pkg/processor/summarizer/sections.go`, `document.go`, `request.go`,
  `execute.go`, `util.go`, and `processor.go` participate in section/document
  summary execution and prompt rendering.
- `pkg/model/layout/chunk.go` stores chunk keywords as `MoleKeysD`/`MoleKeys`,
  section summaries as `SectionMeta.Search`, and document summaries as
  `DocumentMeta.Search`.
- `pkg/model/layout/xray.go` emits document summary differently depending on
  document consistency: a single consistent summary becomes top-level
  `XRay.Summary` / JSON `fileSummary`; divergent document summaries become
  per-chunk `FileSummary` / JSON `fileSummary`.
- `pkg/model/layout/document.go`, `search_meta.go`, `custom_meta.go`, and
  related tests may be needed if custom section/document outputs cannot live on
  fixed chunk fields.
- `pkg/model/layout/xray.go` emits `ChunkKeywords` with JSON tag
  `chunkKeywords`, `SectionSummary` with JSON tag `sectionSummary`, and
  `FileSummary` with JSON tag `fileSummary`.
- `pkg/model/layout/xray_test.go` covers X-Ray `ChunkKeywords`.
- `pkg/model/completions/eyelevel/process.go` loads `Process.Template` into
  prompt templates via `gpt.InitTemplates(...)`.
- `pkg/model/prompt/templates.go` initializes and expands template values for
  prompt rendering.
- `pkg/partner/workflow.go` top-level create/update compatibility paths copy
  `ChunkStrategy`, `Extract`, and `Steps`, but not `Template`; the existing
  `APIRequest.Template` field is a different partner template type, not the
  workflow `*map[string]string` template config.

### internal-arcadia-agents

- `classes/statement.py` includes `chunkKeywords` in the X-Ray output fields
  used by routed reassembly.
- `classes/statement.py` also includes `sectionSummary` and `fileSummary` in
  `XRAY_REASSEMBLY_OUTPUT_ATTRS`.
- `classes/statement.py` builds workflow output by iterating `xray.chunks` and
  the allowlisted chunk attributes; it does not currently route top-level
  `XRayDocument.fileSummary`.
- `classes/extraction_reassembly.py` routes workflow output by
  `workflow_field_paths` and fails preflight on missing groups, invalid route
  maps, or duplicate final paths.
- `tasks/download.py`, `tasks/agent.py`, `tasks/save.py`, and
  `classes/arcadia_agent_request.py` currently implement a hardcoded request
  type graph for reconcile/QA/save operations.
- `classes/test_extraction_reassembly.py` includes a parametrized test that
  verifies metadata can read `chunkKeywords`.
- Runtime metadata must be traced from custom X-Ray/readback output path back to
  final JSON path.

### groundx-studio-harness

- `skills/groundx-extraction-workflows/templates/compile_workflow.py` maps
  `slot: chunk-keys` to SDK attr `chunk_keys`.
- `skills/groundx-extraction-workflows/templates/compile_workflow.py` currently
  exposes a fixed `SLOT_MENU` of `chunk-instruct`, `chunk-keys`, and
  `chunk-summary`; it does not expose custom step arrays or custom output maps.
- `skills/groundx-extraction-workflows/templates/xray_to_extract.py` reads
  `chunkKeywords` for charges, `chunkSummary`/`suggestedText` for meters, and
  `sectionSummary` for statement fields.
- `skills/groundx-extraction-workflows/templates/validate_workflow_json.py`,
  `SKILL.md`, `SKILL.public.md`, `references/*`, `evals/evals.json`,
  examples, changelog entries, and scanner tests enforce or describe the old
  fixed-slot model.
- `skills/groundx-extraction-workflows/references/2_schema_design.md` documents
  `chunk-keys` -> `chunkKeywords`.
- `scripts/tests/test-groundx-extraction-workflows.mjs` validates the old
  three-slot menu and must be updated when custom steps are supported.

## Custom Step Serialization Survival Points

Custom step identity must survive these boundaries without case, kebab, camel,
or enum-name normalization:

- authored extraction YAML: `workflow.custom_steps.<level>[].name`, final group
  `workflow_step`, and field-level `workflow_output_key`
- SDK prepared state: custom step definitions, workflow group assignments,
  canonical route metadata, and `leaf_fields`
- persisted workflow extract metadata: `workflow.metadata_version`, `custom_steps`,
  `output_routes`, `leaf_fields`, optional `field_counts`, and optional
  `schema_hash`
- public workflow config: `customSteps[].name`, `customSteps[].level`,
  `customSteps[].kind`, optional `customSteps[].config`,
  `customSteps[].requiredTemplateKeys`, workflow-level `outputRoutes[]`,
  workflow-level `leafFields[]`, route `outputKey` values, and leaf
  `isRepeated`/`repetitionScope` values for direct non-YAML callers
- cashbot-go model/runtime: custom step names must use a custom-step model path
  rather than the fixed `StepType` enum path, while fixed step names keep the
  existing enum behavior
- runtime storage and X-Ray/readback: custom output maps are keyed by
  `<step_name>/<output_key>` through `customChunkOutputs`,
  `customSectionOutputs`, and `customDocumentOutputs`
- SDK, harness, and Arcadia reassembly: route metadata must map the exact custom
  readback path back to the final JSON path without exposing custom workflow
  group names as final groups

The fixed-output trace follows real runtime paths for the representative chunk,
section, and document outputs: workflow config enters fixed Go step/field enums,
processors write fixed layout fields, X-Ray emits fixed JSON names, and SDK,
harness, or Arcadia read those emitted names. The custom-step plan therefore
adds separate custom-step metadata and custom output maps instead of overloading
the fixed fields or aliases.

## Repo-Plan Verification Questions

Resolved by the locked central contract:

- Custom X-Ray/readback uses `customChunkOutputs`, `customSectionOutputs`, and
  `customDocumentOutputs`.
- Custom document outputs use `customDocumentOutputs`, not legacy top-level or
  per-chunk `fileSummary`.
- Public workflow `template` follows cashbot-go workflow/process
  `Process.Template *map[string]string`; the top-level partner template object
  is not reused.
- One executable workflow step may own at most 20 fields, with public
  API/runtime hard-fail validation mirrored by SDK, harness, and ADP validation.
- Top-level YAML `workflow:` is always reserved for authoring metadata.
- Arcadia keeps `agent` and `save_agents` internal behind the default
  compatibility adapter, treats `qa_charges` as dead legacy, and defers
  `reconcile_fields`, `qa_fields`, and `save_fields` to a follow-on plan.
- SDK/docs publishing is allowed only late, after local verification, as the
  final prerequisite before the e2e path that requires published artifacts.
- Route metadata records `workflow_group`, `workflow_field`, `final_path`,
  `step_name`, `level`, `output_map`, `output_key`, and `readback_path`.
- Public workflow config carries route records as workflow-level `outputRoutes`;
  persisted metadata stores them as `output_routes`.
- Public workflow config carries leaf-field records as workflow-level
  `leafFields`; persisted metadata stores them as `leaf_fields`.
- Public `outputRoutes` and `leafFields` must match one-to-one on final path,
  workflow group/field, custom step, level, and output key before hashing or
  execution.
- YAML explicit output keys use field-level `workflow_output_key`; persisted
  metadata uses `output_key`; public JSON route records use `outputKey`.
- Public `customSteps[]` records contain `name`, `level`, `kind`, optional
  `config`, and optional `requiredTemplateKeys`; custom step `config` reuses the
  existing element-targeted workflow step shape and omits or nulls the legacy
  fixed-output `field`.
- Custom step names are lower snake case (`^[a-z][a-z0-9_]{0,63}$`), globally
  unique, and never auto-normalized from case/kebab/camel variants.
- Custom output `output_key` values follow the same lower-snake-case rule.
- `workflow.metadata_version: 1` is current; unknown/future custom workflow
  metadata versions fail closed.
- Public API/runtime field counts are server-recomputed from canonical
  `workflow.extract.workflow.output_routes` and
  `workflow.extract.workflow.leaf_fields`.
- Leaf-field repetition uses `is_repeated` and `repetition_scope` in persisted
  metadata, and `isRepeated` and `repetitionScope` in public JSON.
- Repeated item leaves use a literal `*` RFC 6901 path segment as a schema
  wildcard, such as `/fees/*/amount`, and count once per prompted schema leaf.
- Template config is `map[string]string`, allows extra keys, blocks reserved
  names and invalid types/sizes, stores YAML-authored values at workflow-level
  `workflow.template`, declares required keys through step metadata, validates
  required keys with the same normalization/rules as template keys, and keeps
  existing fixed-prompt optional placeholder behavior.
- Reserved workflow metadata template key names are enumerated by the
  workflow-config contract and apply equally to `template` and
  `requiredTemplateKeys`.
- TypeScript smoke coverage uses `fern generate --group ts-sdk`.

- The repo-owned `cashbot-go` plan now records the exact storage persistence
  boundary: `layout.CustomMeta` document (`docM`), molecule (`moleM`), and
  section (`sectionM`) maps, with `CustomMeta.Scan`/`Value` as the DB
  serialization boundary and nil/absent metadata treated as empty custom output
  maps for old rows.
- The repo-owned `cashbot-go` plan now records the public workflow create/update
  validation path: `WorkflowHandler.createWorkflow` and
  `WorkflowHandler.updateWorkflow` call `Workflow.ValidateCreate` and
  `Workflow.ValidateEdit`; custom-step, route/leaf, schema-hash, and 20-field
  validation must be reached from both methods.
- The current `internal-arcadia-agents` gate is only a deferral stub. The
  follow-on plan, created after central cleanup/closeout, must define input
  payload, output payload, retry/idempotency, and failure propagation contracts
  for `reconcile_fields`, `qa_fields`, and `save_fields`.

## Trace Commands To Rerun Before Implementation

```bash
rg -n "chunk-keys|chunkKeys|ChunkKeys|chunkKeywords|ChunkKeywords|MoleKeys|SetChunkKeys" \
  /Users/benjaminfletcher/git/eyelevel-fern-config \
  /Users/benjaminfletcher/git/groundx-python \
  /Users/benjaminfletcher/git/cashbot-go \
  /Users/benjaminfletcher/git/internal-arcadia-agents \
  /Users/benjaminfletcher/git/groundx-studio-harness
```

```bash
rg -n "sect-summary|sect-sum|SectSummary|SectionSummary|sectionSummary|SetSectionSummary|doc-summary|doc-sum|DocSummary|DocumentSummary|fileSummary|FileSummary|XRayDocument|SetDocumentSummary|GetDocumentSummary|XRay\\.Summary|XRayChunk\\.FileSummary" \
  /Users/benjaminfletcher/git/eyelevel-fern-config \
  /Users/benjaminfletcher/git/groundx-python \
  /Users/benjaminfletcher/git/cashbot-go \
  /Users/benjaminfletcher/git/internal-arcadia-agents \
  /Users/benjaminfletcher/git/groundx-studio-harness
```

```bash
rg -n "qa_charges|qa_meters|qa_statement|reconcile_charges|reconcile_meters|reconcile_statement|save_charges|save_meters|save_statement|allowed_request_types|next_agent|save_agents|def agent" \
  /Users/benjaminfletcher/git/internal-arcadia-agents
```

```bash
rg -n "Template \\*map\\[string\\]string|template,omitempty|Templates\\(\\)|process.Templates" \
  /Users/benjaminfletcher/git/cashbot-go
```

```bash
rg -n "workflow:|RESERVED_TOP_LEVEL_KEYS|top_level_metadata|workflow_group_metadata|_groundx_persisted_extract|workflow_field_paths|final_field_paths" \
  /Users/benjaminfletcher/git/groundx-python \
  /Users/benjaminfletcher/git/internal-arcadia-agents \
  /Users/benjaminfletcher/git/groundx-studio-harness
```
