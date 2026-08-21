# Proposal: preserve persisted workflow readback

## Execution route

This SDK change is governed by
`internal-arcadia-agents/openspec/changes/complete-extraction-boundary-regression-coverage/tasks.md`.
It is an input to that closeout, not a separate certification path.

## Why

`load_extraction_definition_from_workflow_response()` recompiles an existing
workflow by passing its persisted extract back through the authored-YAML
compiler. That crosses two different boundaries:

- authored YAML is validated and compiled when a workflow is created or updated;
- persisted workflow readback is execution input and must be preserved.

The error blocked two protected workflows before ingest. Arcadia legacy was
rejected because its historical authored snapshot contains
`final_value_aliases`. Generic v1 was rejected because current authoring-chain
coverage rules were applied to its already compiled routes.

## What changes

- Authored paths, YAML text, and authored mappings continue through
  `prepare_extraction_yaml()`.
- Existing workflow responses and mappings explicitly marked
  `mapping_kind="workflow_extract"` receive structural execution-metadata
  validation only.
- Persisted extract bytes are preserved, and readback returns `prepared=None`.
- The reader does not reapply current authoring rules or compare writer-owned
  hashes.

Internal Arcadia already reconstructs its runtime prompt cache and reassembly
metadata from the deployed workflow. It does not need an SDK-authored prepared
object at this boundary.

## Impact

The change affects only existing-workflow readback. Creating or updating a
workflow from authored YAML remains fully compiled and validated. Rollout
requires an SDK release, an Internal Arcadia pin update, and extraction-service
deployment before the protected file replays and closeout capture resume.
