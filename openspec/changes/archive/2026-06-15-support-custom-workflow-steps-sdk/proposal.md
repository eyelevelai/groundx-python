# Support Custom Workflow Steps SDK

## Why

The shared custom workflow-step contract needs a repo-owned Python SDK plan that
can be validated and archived independently from the central cross-repo
coordination plan. The SDK owns generated Python workflow client surfaces after
the approved Fern/OpenAPI path and handwritten `groundx.extract` YAML,
persistence, and X-Ray/readback behavior.

## What Changes

- Add generated-client coverage for workflow-level `template`, `customSteps`,
  `outputRoutes`, `leafFields`, `requiredTemplateKeys`, custom output maps, and
  field-count metadata once the Fern/OpenAPI contract is generated into this
  repo.
- Add handwritten extraction YAML support for `workflow:` authoring metadata,
  custom workflow steps, `workflow_step`, `workflow_output_key`, persisted
  `workflow.extract.workflow` metadata, route/leaf integrity, and 20-field
  mirrored validation.
- Add SDK readback support for `customChunkOutputs`,
  `customSectionOutputs`, and `customDocumentOutputs` while preserving fixed
  fields such as `chunkKeywords`, `sectionSummary`, and `fileSummary`.
- Keep generated files separate from handwritten extract implementation and
  publish the SDK only after upstream runtime/API, schema, harness, and
  TypeScript generation gates pass.

## Impact

- The existing central `support-custom-workflow-steps` change remains a
  coordination artifact and is not the archiveable SDK implementation plan.
- This change is the repo-owned, archiveable Python SDK implementation plan.
- No SDK implementation begins until a clean implementation branch/worktree is
  selected and the generated-file source path is confirmed.
