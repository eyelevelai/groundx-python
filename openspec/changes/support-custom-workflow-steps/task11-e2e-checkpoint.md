# Task 11 End-To-End Checkpoint

## Status

Partially executed. Release remains blocked.

Updated 2026-06-15 after deployed runtime/API guardrail retests, live ingest
attempts, a committed SDK payload fix, and a post-deploy ingest rerun.

## Local Non-Live Evidence

- Legacy YAML selected:
  `/Users/benjaminfletcher/git/groundx-studio-harness/skills/groundx-extraction-workflows/examples/insurance-claim/prompt.yaml`.
- Custom-step YAML selected:
  `/Users/benjaminfletcher/git/adp-poc/workflows/adp_401k_v1/prompt.yaml`.
- Both compiled and passed structural validation through the unpublished local
  SDK/harness worktrees.
- Legacy compiled workflow had no custom workflow metadata.
- ADP custom compiled workflow had 13 custom steps, 159 output routes, and 159
  leaf fields.
- Synthetic ADP X-Ray readback mapped
  `/chunks/*/customChunkOutputs/adp_f1_employer_information/f001_employer_name`
  to final path `/employer_information/employer_name` with value
  `Example Employer LLC`.
- The synthetic ADP final JSON did not leak the custom step name.
- The Arcadia current-wave deferral stub remains in place at
  `/Users/benjaminfletcher/git/internal-arcadia-agents/openspec/notes/support-custom-workflow-steps-deferral.md`.
- Live smoke found that the SDK persisted authored YAML copy carried
  authoring-only `workflow_step` / `workflow_output_key` keys into
  `_groundx_persisted_extract`, which made the deployed layout path fail with
  `unsupported pseudo-group keys`.
- Local SDK fix added a regression so custom workflow `_groundx_persisted_extract`
  is runtime-safe, keeps persisted `workflow.metadata_version: 1`, strips
  authoring-only custom-step keys, and still reloads from persisted route/leaf
  metadata.
- Focused verification after the local SDK fix:
  `poetry run pytest tests/custom/test_extraction_workflow_client_exports.py tests/extract/test_extraction_workflow_definitions.py tests/extract/prompt/test_manager.py tests/extract/prompt/test_persisted_workflow_extract.py -q`
  passed with `93 passed, 5 subtests passed`.

## Live Workflow API Evidence

Using the unpublished local SDK against the deployed API:

- Legacy workflow create/get/delete succeeded.
  - Created workflow ID: `6a530e16-d887-4ca1-8893-0b5a4354db66`
  - Deleted successfully.
  - Readback had no custom workflow metadata.
- Custom ADP workflow create/get/delete succeeded.
  - Created workflow ID: `3fab4070-d719-4b3a-91bc-14caa974f86f`
  - Deleted successfully.
  - Readback preserved `workflow.extract.workflow` with 13 custom steps, 159
    output routes, and 159 leaf fields.
- Negative oversized/spoofed workflow create unexpectedly succeeded.
  - Created workflow ID: `13281022-1fcc-4b61-99fc-83a33f1aebcd`
  - Deleted successfully.
  - The request assigned all 159 ADP output routes to one custom step while
    spoofing `field_counts` to a low value. The deployed API should have
    rejected this before save.
- Cleanup verification found zero remaining workflows with prefix
  `codex-e2e-support-custom-workflow-steps-`.
- Retest after deployment:
  - Valid small custom-step workflow create/delete succeeded.
    - Created workflow ID: `830592ad-32af-4a65-a43b-e03d1ceeebb3`
    - Deleted successfully.
  - Negative 159-field oversized/spoofed workflow did not save, but the API
    disconnected without a response. That is not acceptable release evidence.
  - Negative 21-field oversized/spoofed workflow returned HTTP 400, but the
    message was `Required attribute 'workflow.outputRoutes' is missing or
    empty` rather than a clear 20-field/custom-step guardrail error. That is
    not acceptable release evidence.
  - Cleanup verification again found zero remaining workflows with prefix
    `codex-e2e-support-custom-workflow-steps-`.
- Retest after final deployed cashbot-go guardrail fix:
  - Negative 21-field oversized/spoofed workflow create returned HTTP 400 with
    message `Invalid attribute 'workflow.outputRoutes': custom step
    adp_f1_employer_information has 21 fields; max is 20`.
  - Negative 21-field oversized/spoofed workflow update returned HTTP 400 with
    the same custom-step max-field message.
  - The temporary valid workflow used for the update test was deleted.

## Live Ingest Evidence

Using the local SDK against the deployed API/runtime:

- Representative ADP sanitized PDF attempted:
  `/Users/benjaminfletcher/git/adp-poc/samples/sanitized/ePlan 2A.pdf`.
  - Workflow ID: `29f0d030-b962-477d-8383-0a05f0ba96db`
  - Bucket ID: `29238`
  - Process ID: `0fe08fa0-430b-40c4-9a75-8a4ee9566eff`
  - Document ID: `b68c67fd-02bc-41e0-ad7d-577cb7a75e98`
  - Final document status: `error`
  - Error: `file is too large to process for this subscription level`
  - Cleanup deleted the document, unassigned and deleted the workflow, and
    deleted the bucket.
- Tiny synthetic one-page ADP-style PDF smoke before the local SDK payload fix:
  - Workflow ID: `55828d2a-c0e8-409a-8742-b60c3df2cad5`
  - Bucket ID: `29239`
  - Process ID: `7295167c-46d7-45e0-a597-b8b3912e0277`
  - Document ID: `505aa0b3-eacf-446e-8390-7100f1fb3f42`
  - X-Ray contained `customChunkOutputs` from custom ADP steps.
  - Final extract failed with `unsupported pseudo-group keys at
    [_pseudo_groups.adp_f10_employer_contributions_profit_sharing]:
    ['workflow_step']`.
  - Cleanup deleted the document, unassigned and deleted the workflow, deleted
    the bucket, and deleted the temporary PDF.
- Tiny synthetic one-page ADP-style PDF smoke after the local SDK payload fix:
  - Payload check passed before create:
    `_groundx_persisted_extract.workflow.metadata_version == 1` and the authored
    copy contained no `workflow_step` text.
  - Workflow ID: `d240c6bf-4ed0-4cb8-a0de-0a8ebe603fb1`
  - Bucket ID: `29240`
  - Process ID: `fc5bab86-aaca-413d-a2a0-d82274b7dbd5`
  - Document ID: `6fea60f4-682a-4af2-b214-d5cc0fb0cfdf`
  - X-Ray readback via SDK succeeded.
  - X-Ray contained two `customChunkOutputs` containers.
  - First observed custom output:
    `customChunkOutputs.adp_f10_employer_contributions_profit_sharing.f116_employer_profit_sharing_type`.
  - Route metadata mapped it to final path
    `/employer_contributions/employer_profit_sharing_type`.
  - Final extract failed with `[latest.yaml] is missing a statement entry`.
  - Cleanup deleted the document, unassigned and deleted the workflow, deleted
    the bucket, and deleted the temporary PDF.
- Post-deploy rerun after the final-extract `statement` path was reported
  deployed did not reach document processing:
  - The local branch payload check still passed:
    `_groundx_persisted_extract.workflow.metadata_version == 1` and the authored
    copy contained no `workflow_step` text.
  - Standard `client.ingest(...)` with a normal one-page reportlab PDF uploaded
    the file and then failed before processing with deployed HTTP 400:
    `Required attribute 'document.fileData' is missing or empty`.
  - Retrying with an explicit upload, a 12 second delay, and direct
    `documents.ingest_remote(...)` failed with the same deployed HTTP 400.
  - Generated `documents.ingest_local(...)` also did not provide a usable
    workaround; the deployed API returned HTTP 400:
    `Required attribute 'document or documents' is missing or empty`.
  - Cleanup deleted each temporary bucket/workflow and temporary PDF.
- Cleanup verification found zero remaining buckets and zero remaining documents
  with the `codex-e2e-support-custom-workflow-steps-` prefix.
- Post-deploy cleanup verification found zero remaining buckets, zero remaining
  workflows, and zero remaining documents with the
  `codex-e2e-support-custom-workflow-steps-` prefix.

## Blockers

- The SDK payload fix is committed and pushed in PR #19, but it is not merged or
  released. Published-SDK E2E is still blocked on review, merge, and the next
  `groundx-python` release.
- Live representative ADP ingest is blocked by the current account/subscription
  limit: even the smallest sanitized representative PDF attempted here failed as
  too large for the subscription level.
- The post-deploy rerun cannot verify whether the final-extract/layout
  `statement` assumption is fixed, because ingest now fails before processing
  with `Required attribute 'document.fileData' is missing or empty`.
- The deployed ingest path used by the SDK helper appears incompatible with the
  current API/runtime response path. `client.ingest(...)`,
  `documents.ingest_remote(...)`, and generated `documents.ingest_local(...)`
  all failed before processing a small PDF.
- Local publish credentials such as Fern org access and NPM token are not
  available in this environment; any docs/SDK/TypeScript publish verification
  must be done through the maintainer-owned release path.

## Required Next Step

Merge and release PR #19, resolve the deployed ingest `document.fileData`
failure, then rerun Task 11. If representative ADP ingest remains
subscription-blocked, use an explicitly approved small synthetic ADP PDF as the
deployed-path substitute. Only archive the plan after the rerun either passes or
release governance explicitly accepts substitute evidence.
