## Why

The upstream OpenAPI spec (in `eyelevel-fern-config`) has added `WorkflowTemplate` and the optional `template` field to `WorkflowRequest` (create/update) and `WorkflowDetail` (read). Until the Python SDK is regenerated from the updated spec, callers cannot pass or receive `template` via a declared, typed SDK path — they would have to rely on the `extra="allow"` Pydantic escape hatch, which is undocumented and untested. Regenerating and confirming the SDK surface closes this gap and establishes `template` as a documented, first-class workflow config field in the Python client.

## What Changes

- **ADDED** `WorkflowTemplate = typing.Dict[str, str]` — new generated type alias in `src/groundx/types/`.
- **ADDED** `template: typing.Optional[WorkflowTemplate]` on `WorkflowRequest` — surfaced as a keyword argument on `WorkflowsClient.create(...)` and `WorkflowsClient.update(...)` (and their async counterparts).
- **ADDED** `template: typing.Optional[WorkflowTemplate]` on `WorkflowDetail` — readable on the response object from `create`, `update`, and `get`.
- **ADDED** `WorkflowTemplate` to `src/groundx/types/__init__.py` (generated export list).
- **ADDED** README coverage: a usage example showing `template={...}` in `client.workflows.create(...)`.
- No breaking changes: the field is optional on both request and response; existing callers pass no `template` and are unaffected.

Semver impact: **minor** (additive; no existing public signature removed or changed).

Fern-generated layer confirmation: ALL type and client changes above are produced by Fern regen from the updated `eyelevel-fern-config` OpenAPI spec. The hand-written `.fernignore`-listed paths (`src/groundx/ingest.py`, `src/groundx/csv_splitter.py`, `src/groundx/extract/`) are NOT involved and require no changes. `openspec/` itself is on `.fernignore` and survives regen.

## Capabilities

### New Capabilities

- `workflow-template-sdk-surface`: The Python SDK exposes `WorkflowTemplate` and the `template` field on `WorkflowRequest` / `WorkflowDetail`, enabling callers to pass and read prompt variable maps through typed SDK methods. Covers: Fern regen producing the type + client changes, mypy + pytest verification, and README usage documentation.

### Modified Capabilities

(none — no existing spec-level requirements change)

## Impact

- **Affected generated files (post-regen):** `src/groundx/types/workflow_request.py`, `src/groundx/types/workflow_detail.py`, `src/groundx/types/__init__.py`, `src/groundx/workflows/client.py`, `src/groundx/workflows/raw_client.py`, `reference.md`.
- **Hand-written layer:** unchanged (`ingest.py`, `csv_splitter.py`, `extract/`).
- **README.md:** add a `template` usage example (hand-written, on `.fernignore`, safe to edit).
- **Tests:** no new hand-written tests needed for the Fern-generated surface; `tests/custom/` and `tests/extract/` are unaffected. CI gates (`poetry run mypy .` and `poetry run pytest`) must still pass post-regen.
- **Downstream consumers:** `internal-arcadia-agents` imports `groundx[extract]>=3.4.3` — this change is additive; no pin bump required. `groundx-on-prem` soft-binds via the `eyelevel/extract` image; no impact. `groundx-studio-harness` and `groundx-agent-harness` are reference-only.
- **Semver:** minor version bump on release (additive public surface).
- **Open design questions:** none.
