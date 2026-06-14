# Support Custom Workflow Steps SDK Tasks

## Working State

- Repo scan branch: `codex/support-custom-workflow-steps-plan`.
- Repo scan dirty state: untracked central OpenSpec change folder
  `openspec/changes/support-custom-workflow-steps/` and this repo-owned SDK
  OpenSpec change folder.
- Implementation branch/worktree: create or confirm clean branch
  `codex/support-custom-workflow-steps-sdk` from `origin/main` before code
  changes.
- Fresh-scan correction: the current branch contains generated-folder edits that
  are not allowed in this PR. Treat any completed task that depended on
  generated `src/groundx/types` or `src/groundx/workflows` edits as reopened
  until the generated diffs are removed.
- Commit checkpoints:
  1. failing generated-client serialization and extract YAML tests;
  2. generated-folder cleanup;
  3. handwritten extract YAML and persisted metadata;
  4. X-Ray/readback parsing and full SDK verification;
  5. post-Fern-release generated-client verification when the generated SDK
     surfaces exist.

## Corrective Tasks

- [x] Remove every manual diff under `src/groundx/types`.
- [x] Remove every manual diff under `src/groundx/workflows`.
- [x] Move any required type/schema work to
      `/Users/benjaminfletcher/git/eyelevel-fern-config/fern/openapi.yml`.
- [x] Remove `src/groundx/extract` dependencies on new generated custom workflow
      classes. Use plain dict/list normalization or existing released generated
      types only.
- [x] Keep helper implementation under `src/groundx/extract/*` and
      `src/groundx/ingest.py`.
- [x] Gate create/update helper behavior that needs generated workflow client
      parameters until the Fern-generated SDK release provides them.
- [x] Update tests so this PR validates handwritten helper behavior without
      requiring hand-created generated classes.
- [x] Run
      `git diff --name-only origin/main...HEAD -- src/groundx/types src/groundx/workflows`
      and confirm it prints nothing.
- [x] Run
      `rg -n "from \\.\\.types|from groundx\\.types" src/groundx/extract`
      and confirm no extract helper depends on new generated custom workflow
      classes.
- [x] Re-run SDK OpenSpec, pytest, mypy, and full diff checks after cleanup.

## Tasks

- [x] Create or select clean branch `codex/support-custom-workflow-steps-sdk`
      from `origin/main`.
- [x] Confirm clean implementation state with `git status --short --branch`.
- [x] Add failing generated-client serialization tests in
      `tests/custom/test_client.py` named
      `test_workflow_request_serializes_template_and_custom_steps` and
      `test_workflow_detail_deserializes_custom_routes_and_outputs`.
      Expected before generated update: `WorkflowRequest` and `WorkflowDetail`
      cannot represent the new fields or reject them as unknown extras.
- [x] Add failing extraction YAML tests in
      `tests/extract/prompt/test_manager.py` named
      `test_prepare_extraction_yaml_accepts_custom_workflow_steps`,
      `test_prepare_extraction_yaml_rejects_slot_and_workflow_step_conflict`,
      `test_prepare_extraction_yaml_rejects_reserved_workflow_final_group`,
      `test_prepare_extraction_yaml_rejects_invalid_custom_step_identity`,
      `test_prepare_extraction_yaml_rejects_missing_required_template_keys`,
      and `test_prepare_extraction_yaml_rejects_custom_step_over_20_fields`.
      Expected before implementation: preparation treats `workflow:` as an
      ordinary group, rejects unknown metadata, or drops custom metadata.
- [x] Add failing persisted extract tests in
      `tests/extract/prompt/test_persisted_workflow_extract.py` named
      `test_persisted_custom_workflow_extract_round_trips_routes_and_leaf_fields`,
      `test_persisted_custom_workflow_extract_rejects_unknown_version`,
      `test_persisted_custom_workflow_extract_rejects_route_leaf_mismatch`,
      and `test_persisted_custom_workflow_extract_hash_is_deterministic`.
      Expected before implementation: custom workflow metadata is not preserved
      or is silently ignored.
- [x] Add failing readback tests in `tests/extract/classes/test_groundx.py`
      named `test_xray_loads_custom_output_maps` and in
      `tests/extract/classes/test_document.py` named
      `test_document_preserves_fixed_and_custom_readback_fields`.
      Expected before implementation: custom output maps are unavailable while
      fixed fields still load.
- [x] Consume generated SDK surfaces only through the approved Fern/OpenAPI
      release path; do not hand-edit generated files in this PR.
- [x] Implement extraction YAML parsing for workflow-level `workflow.template`,
      custom step definitions, `workflow_step`, and `workflow_output_key`.
- [x] Implement persisted `workflow.extract.workflow` metadata for
      `metadata_version`, `custom_steps`, `output_routes`, `leaf_fields`,
      optional `field_counts`, and optional `schema_hash`.
- [x] Enforce custom step identity, route/leaf one-to-one integrity, repeated
      item wildcard path semantics, deterministic hash sorting, and mirrored
      20-field validation before sending workflows.
- [x] Preserve legacy `slot:` behavior for existing YAML and fail when `slot`
      and `workflow_step` appear on the same group.
- [x] Add X-Ray/readback parsing for `customChunkOutputs`,
      `customSectionOutputs`, and `customDocumentOutputs`.
- [x] Run `poetry run pytest tests/custom/test_client.py tests/extract/prompt/test_manager.py tests/extract/prompt/test_persisted_workflow_extract.py -q`.
- [x] Run `poetry run pytest tests/extract/classes/test_groundx.py tests/extract/classes/test_document.py -q`.
- [x] Run `poetry run pytest tests/extract -q`.
- [x] Run `poetry run pytest -rP -n auto tests/custom tests/extract`.
- [x] Run `poetry run mypy .`.
- [x] Run `poetry run pytest -rP -n auto .` before release readiness.
- [x] Confirm generated files are absent from this PR, or explicitly produced by
      the approved Fern-generated release path.
- [x] Adversarial review: confirm fixed workflows, old persisted extracts, and
      old X-Ray/readback fields still work and custom behavior is additive.
