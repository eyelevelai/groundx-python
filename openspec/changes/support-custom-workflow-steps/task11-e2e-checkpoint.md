# Task 11 End-To-End Checkpoint

## Status

Partially executed. Release remains blocked.

## Local Non-Live Evidence

- Legacy YAML selected:
  `/Users/benjaminfletcher/git/groundx-studio-harness-support-custom-workflow-steps/skills/groundx-extraction-workflows/examples/insurance-claim/prompt.yaml`.
- Custom-step YAML selected:
  `/Users/benjaminfletcher/git/adp-poc-support-custom-workflow-steps/workflows/adp_401k_v1/prompt.yaml`.
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

## Blockers

- The deployed API does not currently enforce the 20-field executable custom
  step limit against canonical route/leaf metadata. Release e2e cannot pass
  until the runtime/API branch containing that validation is deployed and this
  negative live check rejects the oversized/spoofed request.
- `FERN_TOKEN` / Fern org access and `NPM_TOKEN` are unavailable in the local
  environment, so docs publish and TypeScript package publish remain blocked.
- Live representative document ingest/extract was not run because the deployed
  oversized-step guardrail failed first. Running ingest before that guardrail is
  fixed would not prove release readiness.

## Required Next Step

Deploy or otherwise point e2e at the runtime/API artifact containing the
Task 5 validation, provide the publish credentials/access needed by the
publish-last gate, then rerun Task 11 from the live negative oversized-step
check onward.
