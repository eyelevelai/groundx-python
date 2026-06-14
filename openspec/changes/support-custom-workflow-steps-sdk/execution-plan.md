# groundx-python SDK Execution Plan

## Scope

This repo owns handwritten `groundx.extract` YAML, persistence, convenience
helpers, and readback behavior. API-shape types and generated workflow client
surfaces belong to the upstream Fern/OpenAPI source and arrive in this repo only
through the approved generation/release path. The central
`openspec/changes/support-custom-workflow-steps/` folder remains a cross-repo
coordination artifact; this folder is the repo-owned SDK implementation plan.

## Fresh-Scan Correction

The current implementation branch is not compliant because it contains manual
changes under generated folders:

- `src/groundx/types`
- `src/groundx/workflows`

Those changes will be overwritten by Fern and must be removed from this PR.
The corresponding type definitions and workflow create/update fields must be
declared in `eyelevel-fern-config/fern/openapi.yml`; Fern then regenerates the
Python SDK classes and workflow client parameters. This PR may keep only
handwritten helper logic in preserved files.

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
- Local generated output may be used for verification before public publishing,
  but it must not be copied into this PR as hand-authored implementation.
- Handwritten SDK commits must not directly edit generated files outside the
  approved generation path.
- The approved source for new generated classes such as custom workflow step
  models, route models, leaf-field models, and X-Ray response models is
  `eyelevel-fern-config/fern/openapi.yml`.
- Until the Fern-generated SDK release lands, handwritten helper code must not
  depend on new generated classes that are absent from the released baseline.

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
2. Remove every manual generated-folder edit from this branch.
3. Keep the generated-client shape in Fern/OpenAPI, not in this SDK PR.
4. Keep helper implementation in preserved handwritten files only:
   `src/groundx/extract/*` and `src/groundx/ingest.py`.
5. Replace extract-side imports of new generated classes with plain dict/list
   normalization or existing released generated types only.
6. Gate helper behavior that requires not-yet-generated workflow client
   parameters until the Fern-generated SDK release provides those parameters.
7. Add handwritten YAML parsing for `workflow.template`, custom step
   definitions, `workflow_step`, `workflow_output_key`, and explicit output
   route metadata.
8. Add persisted extract metadata with `workflow.metadata_version: 1`,
   `custom_steps`, `output_routes`, `leaf_fields`, optional `field_counts`, and
   optional `schema_hash`.
9. Enforce custom step identity, reserved metadata names, `slot` /
   `workflow_step` conflict rejection, required template keys, route/leaf
   one-to-one integrity, repeated item wildcard paths, deterministic hash
   sorting, and the 20-field mirrored validation rule.
10. Preserve legacy YAML and persisted extract behavior when custom workflow
   metadata is absent.
11. Add readback parsing for `customChunkOutputs`, `customSectionOutputs`, and
   `customDocumentOutputs` without changing fixed readback field names.
12. Do not commit generated files from this PR unless they are produced by the
    approved Fern-generated release path.

## Corrective Verification

Before this PR can be considered ready, run:

- `git diff --name-only origin/main...HEAD -- src/groundx/types src/groundx/workflows`
  and confirm it prints nothing.
- `rg -n "from \\.\\.types|from groundx\\.types" src/groundx/extract`
  and confirm extract code does not import new custom workflow generated types
  for helper behavior that must survive regeneration.
- Confirm `eyelevel-fern-config/fern/openapi.yml` owns the public schema names
  and workflow request/response fields.

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
