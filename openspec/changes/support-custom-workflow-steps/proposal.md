# Change: Support Custom Workflow Steps

Status: proposed, planning-only

This change folder is the SDK-centered OpenSpec planning artifact for the
cross-repo contract work. It intentionally starts with discovery before
implementation.

This change is not implementation-ready until the discovery trace, public
contract, release gates, and repo-specific plans are reviewed. Code changes must
start from isolated clean branches or worktrees in each target repository so
this cross-repo feature does not mix with unrelated local work.

This central change is a cross-repo planning artifact and must not be archived
as-is into `groundx-python` specs. The spec deltas in this folder are draft
contract slices used to drive discovery and repo-owned planning. Before archive,
durable requirements must move into the owning repo OpenSpec changes and this
central change must either be closed as planning documentation or reduced to
only the `groundx-python`-owned requirements.

## Problem

ADP 401k extraction currently has 159 fields in
`/Users/benjaminfletcher/git/adp-poc/workflows/adp_401k_v1/prompt.yaml`.
Every final section is assigned to `slot: chunk-instruct`. That puts all fields
through one chunk-level extraction slot. There are not enough current chunk-level
slots to split the work safely, and the same limitation will exist for future
section-level and document-level extraction work.

The current platform exposes a fixed workflow step object with named fields
such as `chunk-instruct`, `chunk-keys`, `chunk-summary`, `sect-summary`, and
`doc-summary`. That fixed menu is too small for large structured extraction
schemas. The system also has a `template` setting in
`cashbot-go/pkg/model/summarizer/process.go`, but that setting is not exposed
through the public Fern/OpenAPI/Python SDK workflow config surfaces.

## Goals

- Design a workflow config shape that supports custom arrays of chunk, section,
  and document steps.
- Keep the existing fixed step names and legacy YAML behavior working for
  current customers.
- Expose the existing Go `template` workflow setting through Fern, the Python
  SDK, documentation, and harness guidance.
- Account for the TypeScript SDK generator affected by the shared Fern schema,
  with a mandatory generation smoke check. TypeScript feature documentation and
  examples may be out of scope for the first release, but schema generation
  compatibility is not optional.
- Trace `chunk-keywords`/`chunkKeywords`/`ChunkKeys` end to end, and also trace
  representative section and document summary paths, so the chosen custom output
  map design covers all three levels it promises.
- Preserve authored extraction YAML and custom step metadata in
  `workflow.extract` so runtimes that download the workflow can see it.
- Reserve top-level `workflow:` as authoring metadata and fail clearly if YAML
  tries to use `workflow` as a final output group.
- Keep legacy `slot:` YAML working while making `workflow_step:` the forward
  assignment key for fixed and custom workflow steps.
- Preserve route metadata from custom X-Ray/readback output paths back to final
  JSON paths so downstream reassembly can work.
- Define custom step naming, uniqueness, reserved-name, normalization, output
  destination, persistence-version, and field-load validation rules before any
  implementation begins.
- Use explicit route records with `workflow_group`, `workflow_field`,
  `final_path`, `step_name`, `level`, `output_map`, `output_key`, and
  `readback_path`. Public workflow config carries these as workflow-level
  `outputRoutes`; persisted metadata stores them as `output_routes`.
- Use explicit leaf-field records with `final_path`, `workflow_group`,
  `workflow_field`, `step_name`, `level`, `output_key`, `field_type`,
  `is_repeated`, and `repetition_scope`. Public workflow config carries these as
  workflow-level `leafFields`; persisted metadata stores them as `leaf_fields`.
- Require `outputRoutes` and `leafFields` to match one-to-one on final path,
  workflow group/field, custom step, level, and output key; reject missing, extra,
  duplicate, stale, or mismatched route/leaf metadata before hashing or execution.
- Use a literal `*` path segment as the schema wildcard for repeated item leaves,
  for example `/fees/*/amount`, and count wildcard item leaves once per prompted
  schema leaf rather than once per runtime array element.
- Define public `customSteps[]` records as `name`, `level`, `kind`, optional
  `config`, and optional `requiredTemplateKeys`; `config` reuses the existing
  element-targeted workflow step shape but cannot set the legacy fixed-output
  `field`.
- Author explicit YAML custom output keys with field-level
  `workflow_output_key`, persist them as `output_key`, and expose them in public
  JSON route records as `outputKey`.
- Use `workflow.metadata_version: 1` for custom workflow metadata and fail
  closed on unknown or future custom metadata versions.
- Use server-recomputed field counts from canonical `workflow.extract.workflow`
  `output_routes` and `leaf_fields`; caller-provided counts and hashes are
  non-authoritative hints only, and hash arrays use deterministic identity
  sorting.
- Enforce the executable-step field-load limit in the API/runtime contract and
  mirror that rule in SDK, harness, and ADP validation so direct API users cannot
  bypass the guardrail. The limit is 20 fields per executable workflow step.
- Update `cashbot-go` to load, store, execute, and expose custom step output in
  X-Ray without breaking existing workflow step behavior.
- Update `internal-arcadia-agents` planning so the current reconcile, QA, and
  save task families remain supported except `qa_charges`, which is dead legacy.
  The new `reconcile_fields`, `qa_fields`, and `save_fields` actions belong in a
  follow-on repo-owned plan after this central planning change is cleaned up and
  closed out. The current central plan may record a deferral stub for
  `internal-arcadia-agents`, but it must not require or start that follow-on
  implementation before closeout.
- Update `groundx-studio-harness` extraction/workflow skills, templates,
  scanners, examples, and plugin mirror after the behavior is implemented.
- Update `eyelevel-fern-config` public docs so engineers understand the public
  SDK path without internal harness terms.

## Non-goals

- Do not immediately rewrite the ADP YAML before the platform contract is
  designed and tested.
- Do not weaken, skip, delete, or rewrite existing tests just to make the new
  behavior pass.
- Do not make arbitrary YAML task execution possible in Arcadia. Runtime task
  graph support must be allowlisted.
- Do not remove the current fixed `WorkflowSteps` fields.
- Do not expose harness internals in public documentation.
- Do not make sidecar metadata the only durable source of truth. The authored
  YAML/custom step settings must survive through `workflow.extract`.
- Do not hardcode the ADP plan shape into SDK, Go, Arcadia, harness, or docs.
- Do not publish generated SDKs or public docs early. Publish them only after
  local/runtime/schema/SDK/harness verification, as the final prerequisite for
  the end-to-end proof that requires published artifacts.
- Do not update downstream dependency bounds until the published-artifact
  end-to-end path passes.

## Repositories

Primary plan lives here:

- `/Users/benjaminfletcher/git/groundx-python`

Current implementation planning and follow-on planning cover:

- `/Users/benjaminfletcher/git/eyelevel-fern-config`
- `/Users/benjaminfletcher/git/groundx-python`
- `/Users/benjaminfletcher/git/cashbot-go`
- `/Users/benjaminfletcher/git/internal-arcadia-agents` (deferral stub now;
  follow-on implementation plan after central closeout)
- `/Users/benjaminfletcher/git/groundx-studio-harness`
- `/Users/benjaminfletcher/git/adp-poc`

Each implementation repo must use a clean branch or worktree dedicated to this
change before local files are modified. Existing unrelated branches or dirty
worktrees are blockers unless the user explicitly approves using them.

Repo-owned OpenSpec work must be valid and archiveable in that repo. Do not
create an `openspec/changes/...` folder that contains only an execution plan; if
there is no durable spec delta for a repo, keep tactical notes outside
`openspec/changes/`.

Public API/runtime field-load validation must not trust caller-asserted field
counts. The API/runtime must derive per-executable-step field counts from the
canonical persisted `workflow.extract.workflow.output_routes` and
`workflow.extract.workflow.leaf_fields`, or verify a server-recomputable
integrity record over that same canonical metadata. Custom extraction workflow
requests with missing, unparseable, stale, mismatched, unknown-version, or
caller-only field-count metadata must be rejected before runtime execution rather
than accepted with an unknown or spoofable load.

## Required Order

1. Discovery trace and design proposal.
2. Fern/OpenAPI contract.
3. Repo-specific implementation plans with exact tests and verification gates.
4. Isolated repo branches/worktrees and publish-last release gates.
5. `cashbot-go` runtime support, API validation, persistence, and X-Ray support.
6. Generated Python SDK verification/release path plus hand-written extract YAML
   support.
7. Arcadia prompt manager deferral stub and preservation requirements for
   existing reconcile/QA/save behavior, with `qa_charges` removed from the future
   authorable vocabulary.
8. Harness extraction/workflow skill support.
9. Public SDK and docs publishing after runtime, SDK, and harness behavior are
   verified, as the last prerequisite before final e2e.
10. ADP YAML migration and end-to-end validation against the published artifacts.
11. Follow-on Arcadia fields plan for `reconcile_fields`, `qa_fields`, and
   `save_fields` after this central plan is cleaned up and closed out.

Downstream dependency changes must use a lower bound such as
`groundx-python >= <released version>` rather than hardcoding an exact SDK
version.

Generated SDK changes must originate from the upstream Fern/OpenAPI source and
the approved SDK regeneration or release workflow. Local generated artifacts may
be used for verification, but generated files in `groundx-python` must not be
hand-edited or committed as implementation work unless an approved release path
explicitly produces that commit.

Each implementation task must be followed by an adversarial review before the
next task starts.
