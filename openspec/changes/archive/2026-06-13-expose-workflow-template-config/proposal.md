# Change: Expose Workflow Template Config

Status: implemented for backend, Fern, generated Python SDK, and public docs;
optional harness YAML passthrough deferred.

This change peels off the smallest useful slice from the broader custom
workflow-step work: allow callers to set workflow-level `template` values on
workflow configs through the public API contract, then consume that contract in
docs and generated SDKs. Harness YAML passthrough remains optional follow-up
work.

## Problem

The backend workflow runtime already has a `template` field on the summarizer
process model, but the public workflow create/update and detail schemas do not
expose it on main. That means users cannot rely on a documented, generated SDK
surface such as `client.workflows.create(..., template={...})` even though the
runtime can use template values when present.

The larger custom workflow-step plan also introduces `customSteps`,
`outputRoutes`, and `leafFields`. Those are valuable, but they are not required
to ship the basic workflow-template capability. Keeping `template` bundled with
the larger custom-step contract delays a feature that can be released sooner.

## Goals

- Add workflow-level `template` to public workflow create/update request
  schemas and workflow detail response schemas.
- Keep the schema small and human-readable: a workflow template is an object
  whose values are strings.
- Add backend request-path support for top-level workflow `template` without
  breaking the existing non-workflow API request field that also uses the JSON
  name `template`.
- Populate workflow template values during the production backend request parse
  path, not only inside handler tests that manually construct an `APIRequest`.
  The preferred backend shape is a non-JSON sidecar field such as
  `APIRequest.WorkflowTemplate *map[string]string json:"-"`.
- Reject workflow `template` request bodies whose values are not strings; do not
  silently drop invalid values when decoding the workflow-template sidecar.
- Support workflow create/update bodies where `template` is the only workflow
  process setting being changed. For update, `workflowId` plus `template` must
  be enough.
- Preserve the backend's existing workflow process overlay semantics: update
  merges non-empty template keys into the stored process template, omitted
  template leaves stored template values unchanged, and clear/delete semantics
  are not introduced in this small PR.
- Update the mirrored backend OpenAPI files together so server and lambda
  public surfaces stay in sync.
- Update the Fern/OpenAPI source with `template` only, leaving custom workflow
  step fields out of this slice.
- Update public Python examples only after the generated Python SDK exposes the
  published Fern field.
- Defer all `groundx-python` generated SDK work until after Fern publishes the
  updated contract.
- Optionally update `groundx-studio-harness` YAML compile/deploy templates to
  pass `workflow.template` through once the backend/Fern contract is available.

## Non-Goals

- Do not add `customSteps`, `outputRoutes`, `leafFields`, custom output
  readback, or custom step execution behavior in this change.
- Do not add or promote extraction workflow convenience methods in this change.
- Do not hand-edit generated `groundx-python` SDK files before Fern publishes
  the updated contract.
- Do not publish Python SDK examples before the generated SDK version can accept
  and return `template`.
- Do not update `internal-arcadia-agents` or `adp-poc` unless a follow-up
  consumer change is explicitly requested.
- Do not use the dirty local `cashbot-go` checkout for this PR; create a clean
  main/master-based branch or worktree.
- Do not add a duplicate `json:"template"` field to the shared backend request
  struct.
- Do not prove backend support with only hand-constructed `APIRequest` values;
  tests must exercise the same request parsing path used by live API requests.

## Repositories

Primary planning repo:

- `/Users/benjaminfletcher/git/groundx-python`

Immediate implementation repos:

- `/Users/benjaminfletcher/git/cashbot-go`
  - Backend public OpenAPI mirrors:
    `server/GroundX/openapi.yml` and `lambda/GroundX/openapi.yml`.
  - Runtime verification around the existing
    `pkg/model/summarizer/process.go` `Template` field.
- `/Users/benjaminfletcher/git/eyelevel-fern-config`
  - Public Fern/OpenAPI source: `fern/openapi.yml`.
  - Public docs only after the contract is valid.

Completed after Fern publish:

- `/Users/benjaminfletcher/git/groundx-python`
  - Regenerated workflow request/detail/client surfaces and focused custom
    tests from the published Fern update.

Conditional consumer repo:

- `/Users/benjaminfletcher/git/groundx-studio-harness`
  - Include only if this immediate slice must support authored harness YAML
    such as `workflow.template` and pass it through compile/deploy.
  - Keep this independent from custom workflow-step harness work.

Not in this slice unless separately approved:

- `/Users/benjaminfletcher/git/internal-arcadia-agents`
- `/Users/benjaminfletcher/git/adp-poc`
- `/Users/benjaminfletcher/git/groundx-agent-harness`

## Dependencies And Blockers

- Backend, Fern, and generated Python SDK work is no longer blocked; the Fern
  update has published and `groundx-python` 3.6.4 exposes workflow
  `template`.
- Harness YAML passthrough is deferred because it was not approved for this
  immediate slice.
- Full live e2e with a customer workflow remains environment-dependent, but the
  SDK contract and serialization path now have local coverage.
