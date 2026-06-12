# Support Custom Workflow Steps SDK Tasks

## Working State

- Repo scan branch: `codex/support-custom-workflow-steps-plan`.
- Repo scan dirty state: untracked central OpenSpec change folder
  `openspec/changes/support-custom-workflow-steps/` and this repo-owned SDK
  OpenSpec change folder.
- Implementation branch/worktree: create or confirm clean branch
  `codex/support-custom-workflow-steps-sdk` from `origin/main` before code
  changes.
- Commit checkpoints:
  1. failing generated-client serialization and extract YAML tests;
  2. approved generated SDK surfaces;
  3. handwritten extract YAML and persisted metadata;
  4. X-Ray/readback parsing and full SDK verification.

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
- [x] Consume generated SDK surfaces from the approved Fern/OpenAPI source path;
      do not hand-edit generated files outside that path.
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
- [ ] Run `poetry run pytest tests/custom/test_client.py tests/extract/prompt/test_manager.py tests/extract/prompt/test_persisted_workflow_extract.py -q`.
- [ ] Run `poetry run pytest tests/extract/classes/test_groundx.py tests/extract/classes/test_document.py -q`.
- [ ] Run `poetry run pytest tests/extract -q`.
- [ ] Run `poetry run pytest -rP -n auto tests/custom tests/extract`.
- [ ] Run `poetry run mypy .`.
- [ ] Run `poetry run pytest -rP -n auto .` before release readiness.
- [ ] Commit generated files separately from handwritten extract changes.
- [ ] Adversarial review: confirm fixed workflows, old persisted extracts, and
      old X-Ray/readback fields still work and custom behavior is additive.
