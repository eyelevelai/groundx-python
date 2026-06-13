# Expose Workflow Template Config Tasks

## Working State

- Central planning repo: `/Users/benjaminfletcher/git/groundx-python`
- Central planning branch: `codex/support-custom-workflow-steps-plan`
- Existing larger plan to leave untouched:
  `openspec/changes/add-extraction-workflow-convenience-methods/`
- New template-only change:
  `openspec/changes/expose-workflow-template-config/`
- Release state: `cashbot-go` PR #1492 merged into `hotfix-search-dell`.
- Release state: `eyelevel-fern-config` PR #13 merged into `main` and the
  Python SDK release was published as `groundx` 3.6.4 from Fern commit
  `f0151a00df5bafb2bbde7018796ce09eddd719e6`.
- Release decision: do not include `groundx-studio-harness` in this immediate
  slice. Keep harness YAML passthrough for a follow-up plan unless explicitly
  approved.

## Tasks

- [x] Create a separate OpenSpec change for workflow-template config exposure.
- [x] Validate this OpenSpec change in the central planning repo.
- [x] Create clean implementation branches or worktrees from main/master for
      the immediate repos. Do not use dirty unrelated worktrees.
- [x] In `cashbot-go`, verify current runtime support for
      `pkg/model/summarizer.Process.Template`.
- [x] In `cashbot-go`, verify the existing `APIRequest` top-level
      `json:"template"` field collision and implement the production request
      parser using a non-JSON workflow-template sidecar, such as
      `APIRequest.WorkflowTemplate *map[string]string json:"-"`, while
      preserving non-workflow template routes.
- [x] In `cashbot-go`, do not add duplicate `json:"template"` fields to the
      shared request struct.
- [x] In `cashbot-go`, implement top-level workflow request `template`
      handling for workflow create/update so generated SDK request bodies do
      not get dropped or mis-decoded.
- [x] In `cashbot-go`, reject workflow `template` bodies whose values are not
      strings during production `NewRequest` parsing; do not silently ignore the
      sidecar decode error.
- [x] In `cashbot-go`, preserve and test existing non-empty merge semantics for
      workflow template updates. Omitted template leaves existing template
      values unchanged; non-empty template values overwrite matching keys and
      preserve unrelated keys; clearing/deleting template keys is out of scope
      for this PR.
- [x] In `cashbot-go`, add a `WorkflowTemplate` schema and `template` property
      to both `server/GroundX/openapi.yml` and `lambda/GroundX/openapi.yml`.
- [x] In `cashbot-go`, add or update narrow tests that start from production
      `NewRequest` parsing of an `APIGatewayProxyRequest` body and prove
      workflow create and update JSON with top-level `template` reaches
      `Workflow.Process.Template`. Include template-only create and
      `workflowId` plus template-only update.
- [x] In `cashbot-go`, add request/handler tests proving invalid non-string
      workflow template values fail before the workflow is created or updated.
- [x] In `cashbot-go`, add or update a regression test proving the existing
      non-workflow template request path still decodes as before.
- [x] In `cashbot-go`, run focused Go tests for workflow request/template
      behavior and any process tests touched.
- [x] In `cashbot-go`, run the repo's OpenAPI or API validation gate if present.
- [x] In `cashbot-go`, perform an adversarial review confirming the diff is
      template-only and server/lambda OpenAPI mirrors match.
- [x] In `eyelevel-fern-config`, update `fern/openapi.yml` with only
      `WorkflowTemplate` and workflow `template` fields.
- [x] In `eyelevel-fern-config`, do not include `customSteps`, `outputRoutes`,
      `leafFields`, or custom-step docs in this slice.
- [x] In `eyelevel-fern-config`, verify the branch diff from `origin/main`
      contains the required `WorkflowTemplate`/workflow `template` additions and
      does not contain custom workflow-step schema/docs contamination before
      running generation checks.
- [x] In `eyelevel-fern-config`, run `fern check`.
- [x] In `eyelevel-fern-config`, run SDK generation smoke checks available in
      the repo, including both Python and TypeScript local generation smoke
      checks when the Fern CLI allows them without publish tokens.
- [x] In `eyelevel-fern-config`, do not publish Python SDK examples until the
      regenerated `groundx-python` version accepts the `template` argument.
- [x] In `eyelevel-fern-config`, perform an adversarial review confirming the
      contract is template-only and publish-ready.
- [x] Publish or merge the Fern update through the approved release path.
- [x] After Fern publishes, regenerate or update `groundx-python` from the
      published Fern contract. Do not hand-edit generated files before this.
- [x] Before adding `groundx-python` tests under `tests/custom`, add
      `tests/custom` to `.fernignore` if it is not already protected.
- [x] In `groundx-python`, add focused tests proving
      `client.workflows.create(..., template={...})` and
      `client.workflows.update(..., template={...})` serialize the public field.
- [x] In `groundx-python`, add focused tests proving workflow detail/readback
      exposes `template` as a declared generated field, not only as an allowed
      Pydantic extra.
- [x] In `groundx-python`, run SDK tests and type checks required for generated
      workflow surface changes.
- [x] After the generated Python SDK supports `template`, update public docs
      with Python SDK examples if they were intentionally deferred from the
      Fern contract PR.
- [x] Defer optional `groundx-studio-harness` YAML passthrough; immediate
      harness support was not approved for this template-only closeout and
      belongs in a follow-up if authored harness YAML must pass
      `workflow.template` through compile/deploy.
- [x] Defer harness minimum-SDK checks because harness deploy support was not
      implemented in this immediate slice.
- [x] Leave `groundx-studio-harness` untouched in this closeout; no owning
      references, tests, scanners, or generated plugin mirrors needed updates.
- [x] Run a final cross-repo review and record what shipped, what remains
      deferred, and what is still blocked by the SDK publish dependency.

## Closeout Evidence

- `cashbot-go`: PR #1492 merged into `hotfix-search-dell`.
- `eyelevel-fern-config`: PR #13 merged into `main`; `fern check` passed after
  the docs follow-up with 0 errors and 13 pre-existing warnings.
- `groundx-python`: generated SDK is at release 3.6.4 and `.fern/metadata.json`
  records origin Fern commit `f0151a00df5bafb2bbde7018796ce09eddd719e6`.
- `groundx-python`: `tests/custom/test_workflow_template.py` covers workflow
  create serialization, update serialization, and declared generated
  `WorkflowRequest`/`WorkflowDetail.template` fields.
- `groundx-python` verification:
  - `poetry run pytest -rP tests/custom -q`: 3 passed, 1 skipped.
  - `poetry run ruff check tests/custom/test_workflow_template.py`: passed.
  - `poetry run mypy .`: passed.
  - `poetry run pytest -rP -n auto .`: 163 passed, 2 skipped.
- Deferred: optional `groundx-studio-harness` YAML passthrough remains outside
  this closeout unless separately approved.
