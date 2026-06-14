# groundx-python SDK Execution Plan

## Scope

This repo owns generated Python SDK surfaces after the approved Fern/OpenAPI
generation path and the handwritten `groundx.extract` YAML, persistence, and
readback behavior. The central
`openspec/changes/support-custom-workflow-steps/` folder remains a cross-repo
coordination artifact; this folder is the repo-owned SDK implementation plan.

## Files

- Generated from approved Fern/OpenAPI path only:
  `src/groundx/types/workflow_request.py`,
  `src/groundx/types/workflow_detail.py`,
  `src/groundx/types/workflow_steps.py`,
  `src/groundx/types/workflow_step.py`,
  `src/groundx/types/workflow_step_config.py`,
  `src/groundx/types/__init__.py`,
  `src/groundx/workflows/client.py`, and
  `src/groundx/workflows/raw_client.py`.
- Handwritten extract files:
  `src/groundx/extract/prompt/utility.py`,
  `src/groundx/extract/prompt/manager.py`,
  `src/groundx/extract/classes/groundx.py`,
  `src/groundx/extract/classes/document.py`,
  `src/groundx/extract/__init__.py`, and
  `src/groundx/extract/prompt/__init__.py`.
- Tests:
  `tests/custom/test_client.py`,
  `tests/extract/prompt/test_manager.py`,
  `tests/extract/prompt/test_persisted_workflow_extract.py`,
  `tests/extract/classes/test_groundx.py`, and
  `tests/extract/classes/test_document.py`.

## Generated Boundaries

- Generated SDK files must come from the upstream Fern/OpenAPI source and the
  approved generation or release path.
- Local generated output may be used for verification before public publishing.
- Handwritten SDK commits must not directly edit generated files outside the
  approved generation path.

## Expected Failing Tests

- `tests/custom/test_client.py::test_workflow_request_serializes_template_and_custom_steps`
  fails before generation because `WorkflowRequest` cannot serialize
  `template`, `customSteps`, `outputRoutes`, `leafFields`, or
  `requiredTemplateKeys`.
- `tests/custom/test_client.py::test_workflow_detail_deserializes_custom_routes_and_outputs`
  fails before generation because `WorkflowDetail` cannot deserialize route,
  leaf, and custom output map fields.
- `tests/extract/prompt/test_manager.py::test_prepare_extraction_yaml_accepts_custom_workflow_steps`
  fails before handwritten implementation because `workflow:` and
  `workflow_step` custom metadata are not prepared.
- `tests/extract/prompt/test_manager.py::test_prepare_extraction_yaml_rejects_slot_and_workflow_step_conflict`
  fails before handwritten implementation because conflict validation is absent.
- `tests/extract/prompt/test_manager.py::test_prepare_extraction_yaml_rejects_reserved_workflow_final_group`
  fails before handwritten implementation because reserved `workflow:` behavior
  is not enforced for custom authoring metadata.
- `tests/extract/prompt/test_manager.py::test_prepare_extraction_yaml_rejects_invalid_custom_step_identity`
  fails before handwritten implementation because custom step identity rules are
  absent.
- `tests/extract/prompt/test_manager.py::test_prepare_extraction_yaml_rejects_missing_required_template_keys`
  fails before handwritten implementation because `required_template_keys` are
  not validated against workflow-level `workflow.template`.
- `tests/extract/prompt/test_manager.py::test_prepare_extraction_yaml_rejects_custom_step_over_20_fields`
  fails before handwritten implementation because SDK-side mirrored field-load
  validation is absent.
- `tests/extract/prompt/test_persisted_workflow_extract.py::test_persisted_custom_workflow_extract_round_trips_routes_and_leaf_fields`
  fails before handwritten implementation because custom route and leaf metadata
  are not persisted.
- `tests/extract/prompt/test_persisted_workflow_extract.py::test_persisted_custom_workflow_extract_rejects_unknown_version`
  fails before handwritten implementation because unknown custom metadata
  versions are not fail-closed.
- `tests/extract/prompt/test_persisted_workflow_extract.py::test_persisted_custom_workflow_extract_rejects_route_leaf_mismatch`
  fails before handwritten implementation because one-to-one route/leaf
  validation is absent.
- `tests/extract/prompt/test_persisted_workflow_extract.py::test_persisted_custom_workflow_extract_hash_is_deterministic`
  fails before handwritten implementation because canonical hash sorting is
  absent.
- `tests/extract/classes/test_groundx.py::test_xray_loads_custom_output_maps`
  fails before readback implementation because custom output maps are not
  exposed.
- `tests/extract/classes/test_document.py::test_document_preserves_fixed_and_custom_readback_fields`
  fails before readback implementation because fixed and custom readback fields
  are not modeled together.

## Implementation Steps

1. Add the expected failing tests listed above without changing production code.
2. Consume generated SDK surfaces from the approved Fern/OpenAPI branch or
   approved local generation output.
3. Add handwritten YAML parsing for `workflow.template`, custom step
   definitions, `workflow_step`, `workflow_output_key`, and explicit output
   route metadata.
4. Add persisted extract metadata with `workflow.metadata_version: 1`,
   `custom_steps`, `output_routes`, `leaf_fields`, optional `field_counts`, and
   optional `schema_hash`.
5. Enforce custom step identity, reserved metadata names, `slot` /
   `workflow_step` conflict rejection, required template keys, route/leaf
   one-to-one integrity, repeated item wildcard paths, deterministic hash
   sorting, and the 20-field mirrored validation rule.
6. Preserve legacy YAML and persisted extract behavior when custom workflow
   metadata is absent.
7. Add readback parsing for `customChunkOutputs`, `customSectionOutputs`, and
   `customDocumentOutputs` without changing fixed readback field names.
8. Commit generated files separately from handwritten extract changes.

## Verification Commands

- `git status --short --branch`
- `poetry run pytest tests/custom/test_client.py tests/extract/prompt/test_manager.py tests/extract/prompt/test_persisted_workflow_extract.py -q`
- `poetry run pytest tests/extract/classes/test_groundx.py tests/extract/classes/test_document.py -q`
- `poetry run pytest tests/extract -q`
- `poetry run pytest -rP -n auto tests/custom tests/extract`
- `poetry run mypy .`
- `poetry run pytest -rP -n auto .`
- `OPENSPEC_TELEMETRY=0 npx @fission-ai/openspec@1.3.1 validate support-custom-workflow-steps-sdk --strict`

## Publish-Last Gate

Do not publish the Python SDK until Fern/OpenAPI, cashbot-go runtime/API,
handwritten extract behavior, harness compile/readback, and TypeScript
generation smoke have passed. If the final e2e requires a published SDK, publish
only as the final prerequisite and do not allow downstream dependency bumps
until that published-artifact e2e passes.
