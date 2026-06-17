## Why

The ADP 401k extraction YAML assigns many field categories to the same fixed workflow slots, overloading those steps and making per-category debugging impossible. The Fern regen from eyelevel-fern-config (commit c015d08) delivered new optional workflow-config schemas (`CustomWorkflowStep`, `WorkflowTemplate`, `CustomWorkflowOutputRoute`, `CustomWorkflowLeafField`, and custom X-Ray output maps) to the generated client. The groundx-python hand-written layer (`src/groundx/extract/`) has no knowledge of these new types yet — they must be wired in so consumers can author, serialize, and read back per-step custom outputs.

## What Changes

- **Fern client regen (INDEPENDENT/CONSUMER side):** absorb the regenerated Fern client carrying the new workflow-config types. No hand-editing of generated code. The new types (`CustomWorkflowStep`, `WorkflowTemplate`, `CustomWorkflowOutputRoute`, `CustomWorkflowLeafField`, `CustomWorkflowStepConfig`, `CustomWorkflowStepElementConfig`, `CustomWorkflowOutputMap`) are available once regen runs and the SDK is rebuilt.
- **Custom step authoring + serialization (FR3):** extend the extract authoring path so `PromptManager`/`prepare_extraction_yaml` can carry `template` (a `WorkflowTemplate` key/value map) and `customSteps[]` authored in YAML through the submit→persist→run→readback cycle. The authored YAML step metadata must survive the `_groundx_persisted_extract` round-trip.
- **Fail-fast validation at submit:** when the extract layer constructs the workflow config, validate custom step fields (name pattern `^[a-z][a-z0-9_]{0,63}$`, level enum, kind enum) and reject invalid/unknown config at build time — not at groundx-api execution time.
- **Custom X-Ray output parsing (FR4):** extend `Chunk`, `XRayDocument`, and `GroundXDocument` readback classes in `src/groundx/extract/classes/groundx.py` to parse the new optional fields `customChunkOutputs`, `customSectionOutputs` (on `DocumentXrayChunk`), and `customDocumentOutputs` (on `DocumentXray`) so each custom step's outputs are individually accessible for per-step debugging. The host schemas use `additionalProperties:true` — the consumer is a tolerant reader.
- **No change to fixed-slot paths:** all nine existing `WorkflowSteps` slots, all existing `prepare_extraction_yaml` logic, and all existing readback behavior are unchanged — strictly additive.

## Capabilities

### New Capabilities

- `custom-workflow-step-authoring`: Author, validate, and serialize `template` + `customSteps[]` (+ optional `outputRoutes[]` / `leafFields[]`) through the extract prepare/persist/submit path; field-level validation (name regex, level/kind enum) raised at submit; authored metadata survives `_groundx_persisted_extract` round-trip.
- `custom-xray-output-parsing`: Parse `customChunkOutputs`, `customSectionOutputs`, `customDocumentOutputs` from the X-Ray JSON into `Chunk` / `XRayDocument` classes as tolerant-reader optional fields; expose each custom step's output dict for per-step debugging.

### Modified Capabilities

- `extract-yaml`: `PreparedExtractionYaml` gains two new optional fields (`custom_template` and `custom_steps`) that the PromptManager passes through to the workflow request. The round-trip scenario must cover these new fields. Existing scenarios remain valid.

## Impact

- **Hand-written surfaces touched** (all within `.fernignore`):
  - `src/groundx/extract/prompt/utility.py` — `PreparedExtractionYaml` dataclass gains `custom_template` + `custom_steps` + `output_routes` + `leaf_fields`; `prepare_extraction_yaml` parses a `_custom_steps` / `_template` top-level key from YAML and validates step names/enums.
  - `src/groundx/extract/prompt/manager.py` — passes the new fields from `PreparedExtractionYaml` into the `WorkflowRequest` (or workflow update) payload at submit time.
  - `src/groundx/extract/classes/groundx.py` — `Chunk` gains `customChunkOutputs: Optional[Dict[str, Any]]` and `customSectionOutputs: Optional[Dict[str, Any]]`; `XRayDocument` gains `customDocumentOutputs: Optional[Dict[str, Any]]`. `model_config` on these models must be `extra="allow"` (tolerant reader).
- **Generated surfaces** (NOT hand-edited — consumed after Fern regen):
  - `src/groundx/types/` — new types land here on regen; `WorkflowDetail` / `WorkflowRequest` gain the new optional fields.
- **Downstream consumers affected:**
  - `internal-arcadia-agents` — imports `groundx[extract]`; will adopt new surface lazily (no forced migration). Pin bump required after SDK release.
  - `groundx-studio-harness` — `groundx-extraction-workflows` skill updated to reference new custom step/template/output shapes.
- **Semver:** additive new optional fields; no existing public surface removed or renamed. Minor version bump (`3.7.0`) appropriate; no breaking change.
- **Quality gates:** `poetry run mypy .` + `poetry run pytest -rP -n auto .` must pass. New behavior gets new tests under `tests/extract/`.

## Open design questions

none
