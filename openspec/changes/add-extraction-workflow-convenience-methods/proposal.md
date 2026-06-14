# Change: Add Extraction Workflow Convenience Methods

Status: proposed, planning-only

This change adds a small SDK-owned convenience layer over the existing workflow
create/update/get API. It is intentionally separate from
`support-custom-workflow-steps`: that change owns the low-level API/runtime
contract, while this change owns the caller ergonomics for loading extraction
definitions from YAML or existing workflows, then creating and updating
extraction workflows from those definitions.

## Problem

The current public Python examples require callers who want to create or update
an extraction workflow from YAML to:

1. read a YAML file into text,
2. call `prepare_extraction_yaml(...)`,
3. pull out `prepared.persisted_workflow_extract`,
4. inspect `workflow_extract["workflow"]`,
5. manually copy `template`, `custom_steps`, `output_routes`, and
   `leaf_fields`, and
6. call `client.workflows.create(...)` or `client.workflows.update(...)`.

That is too much ceremony for the common path. It also exposes generated
workflow schema details and teaches users to reproduce fragile metadata-copying
logic that the SDK can own.

There is also no promoted high-level way to load an extraction definition from
an existing workflow ID. That leaves humans and automation such as
`internal-arcadia-agents` choosing between low-level workflow responses,
`PreparedExtractionYaml`, and hand-built dictionaries even when their job is
simply "load the extraction definition I should inspect or reuse."

## Goals

- Add `GroundX.create_extraction_workflow(...)` and
  `GroundX.update_extraction_workflow(...)` in the hand-written Python SDK
  surface.
- Add `GroundX.load_extraction_definition_from_yaml(...)` for loading an
  extraction definition from YAML path, YAML text, mapping, or an existing
  prepared object.
- Add `GroundX.load_extraction_definition_from_workflow(...)` for loading an
  extraction definition from an existing workflow ID.
- Add async parity on `AsyncGroundX`.
- Document the promoted create, update, YAML-load, and workflow-ID-load methods
  as first-class hand-written SDK helpers, matching the treatment of `ingest`
  and `ingest_directories` rather than only showing them in a walkthrough
  snippet.
- Make the promoted YAML-load/create/update path path-first while still
  supporting explicit YAML text, mapping, and already prepared inputs for tests
  and advanced callers.
- Treat `mapping` input as authored YAML-shaped by default. Persisted or
  execution workflow `extract` mappings require an explicit advanced
  `mapping_kind="workflow_extract"` argument so the SDK never guesses between
  two dict shapes that can look identical.
- Validate workflow template values as strings. Template keys and values must
  preserve the existing API contract, including placeholder-style keys such as
  `{{LANGUAGE}}` and `{{LANGUAGE_UNKNOWN}}`, including empty-string values.
- Preserve the base SDK experience for users who installed `groundx` without
  the `extract` extra. The exported `GroundX` client must remain importable and
  non-extraction methods must keep working; extraction definition methods may
  lazy-import extract dependencies and raise a clear install hint when
  `groundx[extract]` is missing.
- Keep `prepare_extraction_yaml(...)` and `PreparedExtractionYaml` as the
  lower-level API because `PromptManager`, Arcadia, and tests use the richer
  prepared metadata surfaces.
- Keep `load_from_yaml(...)`, `load_from_mapping(...)`, and
  `group_from_mapping(...)` available as low-level conversion helpers, but do
  not promote them as the recommended extraction workflow API.
- Keep workflow-create/update kwargs assembly as private implementation detail
  or advanced-only plumbing, not as a promoted public technique.
- Hide generated `CustomWorkflowStep*`, route, and leaf-field classes from the
  normal extraction workflow creation path.
- Update public docs and harness templates so they teach the one-call path
  and promoted load-definition path instead of manual workflow metadata
  assembly.
- Update the harness public extraction-doc source of truth so it no longer
  teaches `prepare_extraction_yaml(...)` as the primary public create/update
  path.
- Preserve old direct generated-client access for advanced users.

## Non-Goals

- Do not rename Fern/OpenAPI schemas such as `CustomWorkflowStepConfig` in this
  change. Renaming generated schemas would churn public SDK imports and should be
  a separate contract-cleanup plan if desired.
- Do not add a new server endpoint. The helper delegates to existing workflow
  create/update API calls.
- Do not publish a new SDK or public docs before the custom workflow-step
  runtime/API e2e blocker is resolved.
- Do not remove `workflow_sdk_kwargs(...)` from the harness until the minimum
  released SDK version includes the new convenience methods.
- Do not force `internal-arcadia-agents` to replace specialized metadata-key
  preparation where the helper cannot preserve equivalent behavior.
- Do not implicitly assign created workflows to buckets or accounts. Bucket and
  account assignment remain explicit workflow API calls.
- Do not make workflow execution/testing part of this convenience API. Running
  extraction remains a separate runtime operation after a workflow exists and is
  assigned.
- Do not change the GroundX Studio web UI base experience. Authenticated product
  UI remains the default scaffold shape; onboarding is a configurable overlay on
  top of that authenticated experience, not a separate base app architecture.

## Repositories

Primary OpenSpec planning repo:

- `/Users/benjaminfletcher/git/groundx-python`

Implementation and documentation repos:

- `/Users/benjaminfletcher/git/groundx-python-support-custom-workflow-steps-sdk`
- `/Users/benjaminfletcher/git/eyelevel-fern-config`
- `/Users/benjaminfletcher/git/groundx-studio-harness-support-custom-workflow-steps`
- `/Users/benjaminfletcher/git/internal-arcadia-agents`

Scan-only or conditional repos:

- `/Users/benjaminfletcher/git/adp-poc`
- `/Users/benjaminfletcher/git/groundx-studio-harness`
- `/Users/benjaminfletcher/git/cashbot-go`

Out of scope:

- `/Users/benjaminfletcher/git/groundx-agent-harness` is generated from GroundX
  Studio Harness and must not be edited directly for this plan.

`cashbot-go` is expected to need no change because this convenience layer does
not alter the runtime or public HTTP contract. If implementation reveals a
missing runtime/API behavior, stop and route that through the existing
`support-custom-workflow-steps` blocker instead of patching it here.

## Dependencies And Blockers

- Local SDK/harness/docs changes may be planned and implemented against the
  current custom workflow-step branches.
- Before implementation starts, refresh each implementation branch against its
  current target branch. The existing support-custom-workflow-step branches were
  created before the template closeout PRs merged, so the convenience-method
  work must not proceed from stale branch assumptions. This freshness gate
  includes SDK, Fern docs, GroundX Studio Harness, Arcadia, and ADP before it is
  edited.
- Publishing and downstream dependency bumps remain blocked until the existing
  `support-custom-workflow-steps` deployed-path validation blocker is resolved:
  the deployed API must reject oversized or spoofed custom-step workflows.
- Public docs and harness helper-preference changes may be prepared as draft
  PRs, but they must not merge until the Python SDK helpers have been merged,
  published, and verified from the published package in a fresh environment.
- GroundX Studio Harness updates must follow the harness source-of-truth model:
  update owning skill references, evals, scanner expectations, routing/source
  manifests, generated mirrors, and version surfaces when the change touches
  those contracts. Do not rely on prose-only guidance for repeated invariants.
- New hand-written SDK tests under `tests/custom` must be protected by the SDK
  regeneration boundary before they are added. `.fernignore` is the authoritative
  boundary for files that must survive Fern releases.
