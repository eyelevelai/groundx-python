# Workflow Template Config Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILLS: Use
> `superpowers:test-driven-development` for each code task and
> `superpowers:verification-before-completion` before claiming completion.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship workflow-level `template` support as a small main-branch feature
without dragging in custom workflow steps, output routes, leaf fields, or
extraction workflow convenience methods.

**Architecture:** Expose `template` at the public workflow API contract layer
first, including backend request-path handling for the top-level
`WorkflowRequest.template` field. Mirror that field into Fern, publish the Fern
update, then let generated SDKs pick up the field through the normal generation
path. Harness YAML passthrough is an optional consumer phase that should only
pass the same template map through; it must not enable custom-step behavior.

**Tech Stack:** Go backend/OpenAPI, Fern OpenAPI/docs, generated Python SDK
after Fern publish, GroundX Studio Harness Python templates if the optional
harness phase is approved.

---

## Ground Rules

- This is a template-only detour from the larger custom workflow-step plan.
- Do not add `customSteps`, `outputRoutes`, `leafFields`, custom output
  readback, or custom-step runtime behavior.
- Do not add `create_extraction_workflow`, `update_extraction_workflow`, or
  extraction definition loaders in this plan.
- Do not hand-edit generated `groundx-python` files before Fern publishes the
  updated contract.
- Do not publish Python SDK examples until a generated SDK version actually
  accepts `template`.
- Do not assume the backend top-level JSON name `template` is free. The shared
  `APIRequest` model already has a non-workflow `template` field, so workflow
  request-path handling must be explicit and regression-tested.
- Do not add duplicate `json:"template"` fields to `APIRequest`. Route-specific
  workflow template parsing must happen during production request parsing. The
  preferred shape is a non-JSON sidecar such as
  `APIRequest.WorkflowTemplate *map[string]string json:"-"`, populated from the
  raw request body for workflow routes.
- Do not silently ignore workflow-template sidecar decode failures. If a
  workflow request includes a `template` object with any non-string value, the
  request must fail before create/update changes state.
- Preserve existing workflow process overlay semantics for this small PR:
  non-empty template updates merge into the stored template map, matching keys
  are overwritten, unrelated keys remain, omitted template leaves existing
  template unchanged, and explicit clear/delete semantics are out of scope.
- Do not prove backend support only by manually constructing `APIRequest`
  values. At least one create test and one update test must enter through
  `NewRequest` or the exact production request decoder.
- Template-only workflow config changes are in scope. For update, `workflowId`
  plus top-level `template` must be a valid request.
- Do not use the dirty local `cashbot-go` checkout on `hotfix-search-dell`.
  Create a clean main/master-based branch or worktree.
- Keep every repo diff narrow enough to review as a small PR.
- Run an adversarial review after each repo checkpoint.
- Return to the larger existing plan only after this template-only plan is
  either merged or deliberately paused.

## Phase 0: Plan Baseline

**Repo:** `/Users/benjaminfletcher/git/groundx-python`

**Files:**

- Create:
  `openspec/changes/expose-workflow-template-config/proposal.md`
- Create:
  `openspec/changes/expose-workflow-template-config/tasks.md`
- Create:
  `openspec/changes/expose-workflow-template-config/execution-plan.md`
- Create:
  `openspec/changes/expose-workflow-template-config/specs/workflow-template-config/spec.md`

- [x] Create the OpenSpec change.

- [x] Validate it:

  ```bash
  cd /Users/benjaminfletcher/git/groundx-python
  OPENSPEC_TELEMETRY=0 npx @fission-ai/openspec@1.3.1 validate expose-workflow-template-config --strict
  ```

  Expected: `Change 'expose-workflow-template-config' is valid`.

## Phase 1: cashbot-go Backend Contract

**Repo:** `/Users/benjaminfletcher/git/cashbot-go`

**Branch/worktree:**

- Create a clean branch from `origin/master`, for example
  `codex/expose-workflow-template-config-runtime`.
- If the existing checkout is dirty, create a separate worktree instead of
  reusing it.

**Files:**

- Modify: `server/GroundX/openapi.yml`
- Modify: `lambda/GroundX/openapi.yml`
- Read/verify: `pkg/model/summarizer/process.go`
- Modify if needed: `pkg/partner/request.go`
- Modify: `pkg/partner/workflow.go`
- Test: `pkg/partner/request_test.go`
- Test: `pkg/partner/workflow_test.go`
- Test or modify if needed: `pkg/model/summarizer/process_test.go`
- Test or modify if request decode changes require it:
  `pkg/partner/template_test.go`

### Task 1.1: Verify Runtime And Request Namespace Before Editing API Docs

- [ ] Run:

  ```bash
  cd /Users/benjaminfletcher/git/cashbot-go
  rg -n 'Template .*json:"template,omitempty"|SetTemplates|InitTemplates\\(prc.Template\\)' \
    pkg/model/summarizer pkg/model/completions pkg/processor
  rg -n 'Template .*json:"template,omitempty"|apirequest.Template|apirequest.Workflow.Process == nil' \
    pkg/partner/request.go pkg/partner/workflow.go
  ```

  Expected: `pkg/model/summarizer/process.go` has a JSON `template` field and
  completion setup uses it to initialize prompt templates. Also expected:
  `pkg/partner/request.go` already has a top-level `json:"template"` field for
  non-workflow requests, so workflow template support needs explicit
  request-path handling.

- [ ] If the runtime scan does not show JSON template support, stop and create
      a runtime task before touching public schemas.

- [ ] If the request namespace scan shows the existing `APIRequest.Template`
      field is not a `map[string]string`, do not route workflow templates
      through it blindly.

- [ ] Do not add a second `json:"template"` field to `APIRequest`. Add a
      non-JSON sidecar field instead:

  ```go
  WorkflowTemplate *map[string]string `json:"-"`
  ```

- [ ] Populate that sidecar in the production request path. In
      `pkg/partner/request.go`, `NewRequest` already parses `req.Route` before
      unmarshalling `event.Body`, so workflow-route parsing can decode the raw
      body into a tiny route-specific struct after the normal body unmarshal:

  ```go
  var workflowBody struct {
      Template *map[string]string `json:"template"`
  }
  ```

  Only assign `req.WorkflowTemplate = workflowBody.Template` for workflow
  routes. Do not use this sidecar for non-workflow template routes, and do not
  change the existing `APIRequest.Template *Template json:"template,omitempty"`
  field.

- [ ] If the route-specific sidecar decode fails because `template` is not an
      object or because any template value is not a string, return a request
      parse error before any workflow handler runs. Use the repo's existing
      request-validation style, for example:

  ```go
  return req, errorInvalidField("template", "must be an object with string values")
  ```

  Do not swallow this error just because the normal `APIRequest` unmarshal
  succeeded. The normal unmarshal can ignore unknown fields inside the existing
  non-workflow `Template` struct, so the sidecar decode is the validation point
  for workflow template values.

### Task 1.2: Implement Backend Workflow Request Template Handling

- [ ] Update workflow create/update handling so a public `WorkflowRequest`
      body with top-level `template` reaches `apirequest.Workflow.Process.Template`.
      The workflow handlers should read from `apirequest.WorkflowTemplate`, not
      from `apirequest.Template`, because `apirequest.Template` belongs to
      non-workflow template routes.
      The generated SDK create body shape to support is:

  ```json
  {
    "template": {
      "statement_hint": "Prefer normalized account summary values."
    }
  }
  ```

- [ ] Support update bodies where `workflowId` plus top-level `template` is the
      entire workflow config update:

  ```json
  {
    "workflowId": "00000000-0000-0000-0000-000000000001",
    "template": {
      "statement_hint": "Prefer normalized account summary values."
    }
  }
  ```

- [ ] Preserve existing process overlay behavior for template updates:
      - Omitted `template` leaves the stored template map unchanged.
      - A non-empty `template` map merges into the stored map.
      - Matching keys are overwritten by the update.
      - Unrelated existing keys are preserved.
      - Empty-object clear/delete semantics are not added in this PR.

- [ ] Update the create/update missing-field guards so top-level workflow
      `template` counts as a workflow process setting, the same way
      `extract` and `steps` do.

- [ ] When `apirequest.WorkflowTemplate != nil`, ensure
      `apirequest.Workflow.Process` exists and assign:

  ```go
  apirequest.Workflow.Process.Template = apirequest.WorkflowTemplate
  ```

- [ ] Preserve nested `workflow.template` support if it already works through
      `apirequest.Workflow.Process.Template`.

- [ ] Preserve existing non-workflow template route decoding. If request decode
      code changes, add a regression test around the existing template route or
      shared `APIRequest` decode behavior.

### Task 1.3: Add Backend OpenAPI Template Field

- [ ] Add this schema near the workflow schemas in both OpenAPI mirrors:

  ```yaml
    WorkflowTemplate:
      type: object
      description: Workflow-level prompt template values used by workflow step prompts.
      additionalProperties:
        type: string
  ```

- [ ] Add this property to both `WorkflowDetail.properties` blocks:

  ```yaml
        template:
          $ref: '#/components/schemas/WorkflowTemplate'
  ```

- [ ] Add this property to both `WorkflowRequest.properties` blocks:

  ```yaml
        template:
          $ref: '#/components/schemas/WorkflowTemplate'
  ```

- [ ] Confirm no custom workflow-step fields were added:

  ```bash
  rg -n 'customSteps|outputRoutes|leafFields|requiredTemplateKeys' \
    server/GroundX/openapi.yml lambda/GroundX/openapi.yml
  ```

  Expected: no matches from this template-only change.

### Task 1.4: Add Narrow Backend Tests

- [ ] Add or update tests in `pkg/partner/workflow_test.go` proving create and
      update JSON with top-level `template` reaches the stored workflow process.
      These tests must start from production request parsing, not from a
      hand-populated `APIRequest`:

  ```go
  func Test_WorkflowHandler_createWorkflowPreservesTopLevelTemplateFromJSON(t *testing.T) {
      // Build an APIGatewayProxyRequest for the workflow route whose body has
      // only top-level "template"; call NewRequest to produce APIRequest.
      // Call WorkflowHandler.createWorkflow.
      // Assert the created workflow's Process.Template contains the authored key.
      // Assert the response workflow includes the same template.
  }

  func Test_WorkflowHandler_updateWorkflowPreservesTopLevelTemplateFromJSON(t *testing.T) {
      // Build an APIGatewayProxyRequest for the workflow route whose body has
      // workflowId and only top-level "template"; call NewRequest.
      // Call WorkflowHandler.updateWorkflow.
      // Assert cbdbConn.Workflows[wfid].Process.Template contains the authored key.
      // Assert the response workflow includes the same template.
  }
  ```

- [ ] Add a focused `pkg/partner/request_test.go` regression proving
      `NewRequest` populates `APIRequest.WorkflowTemplate` for a workflow-route
      body like:

  ```json
  {"template":{"statement_hint":"Prefer normalized account summary values."}}
  ```

  Expected: `req.WorkflowTemplate["statement_hint"]` is set. This test must not
  use `json.Unmarshal` directly as the only proof.

- [ ] Add a focused `pkg/partner/request_test.go` regression proving
      `NewRequest` rejects workflow-route template values that are not strings:

  ```json
  {"template":{"statement_hint":123}}
  ```

  Expected: `NewRequest` returns a non-nil error equivalent to
  `errorInvalidField("template", "must be an object with string values")`, and
  the workflow handler is not called.

- [ ] Add update merge-semantics coverage in `pkg/partner/workflow_test.go`:
      start from a stored workflow whose `Process.Template` contains
      `{"statement_hint":"old","keep":"same"}`, update through production
      `NewRequest` with:

  ```json
  {
    "workflowId": "00000000-0000-0000-0000-000000000001",
    "template": {
      "statement_hint": "new"
    }
  }
  ```

  Expected after update: `statement_hint` is `"new"` and `keep` is still
  `"same"`.

- [ ] Add update omission coverage proving a workflow update that omits
      `template` does not clear an existing stored template map.

- [ ] Add or keep a regression test proving create/update without `template`
      still behaves as before.

- [ ] If request decoding changed in `pkg/partner/request.go`, add a regression
      test proving the existing non-workflow template request shape still
      decodes into `APIRequest.Template`.

- [ ] Add a static regression assertion or review check proving
      `pkg/partner/request.go` has only one `json:"template"` field and one
      workflow-template sidecar with `json:"-"`.

- [ ] Add a `pkg/model/summarizer/process_test.go` test only if handler tests do
      not already prove `Process.Template` copy/overwrite behavior. Do not use a
      model-only test as the sole proof for this feature.

- [ ] Run focused tests:

  ```bash
  go test ./pkg/partner ./pkg/model/workflow ./pkg/model/summarizer
  ```

  Expected: pass.

### Task 1.5: Backend Verification And Review

- [ ] Run the smallest repo API/OpenAPI validation command available. If no
      dedicated command exists, record that only mirrored OpenAPI diff review
      and focused Go tests were run.

- [ ] Compare the two OpenAPI mirrors:

  ```bash
  diff -u \
    <(sed -n '/WorkflowTemplate:/,/WorkflowResponse:/p' server/GroundX/openapi.yml) \
    <(sed -n '/WorkflowTemplate:/,/WorkflowResponse:/p' lambda/GroundX/openapi.yml)
  ```

  Expected: no meaningful drift between server and lambda workflow schemas.

- [ ] Adversarial review checkpoint:
  - Is the diff template-only?
  - Did it avoid custom-step fields?
  - Does top-level workflow request `template` reach `Process.Template` through
    production `NewRequest` parsing, not only a hand-built `APIRequest`?
  - Did the existing non-workflow `template` request path stay intact?
  - Are server and lambda OpenAPI surfaces synchronized?

## Phase 2: eyelevel-fern-config Contract

**Repo:** `/Users/benjaminfletcher/git/eyelevel-fern-config`

**Branch/worktree:**

- Create a clean branch from `origin/main`, for example
  `codex/expose-workflow-template-config-fern`.
- Do not reuse a checkout or branch that already contains the larger
  `support-custom-workflow-steps` diff. Before editing, verify the branch base:

  ```bash
  git status --short --branch
  git diff --name-only origin/main...HEAD
  ```

  Expected before edits: clean status on the new branch, with no inherited
  custom-step files in the diff.

**Files:**

- Modify: `fern/openapi.yml`
- Modify only after contract validation: relevant `fern/pages/*.mdx` docs that
  mention workflow create/update with template values.
- Read: `README.md`
- Read: `fern/generators.yml`

### Task 2.1: Add Fern OpenAPI Template Field

- [ ] Add the same `WorkflowTemplate` schema and `template` properties to
      `fern/openapi.yml` that were added to `cashbot-go`.

- [ ] Confirm the field set is template-only:

  ```bash
  git diff --unified=0 origin/main...HEAD -- fern/openapi.yml | \
    rg 'WorkflowTemplate|^[+].*template:'

  git diff --unified=0 origin/main...HEAD -- fern/openapi.yml | \
    rg 'customSteps|outputRoutes|leafFields|requiredTemplateKeys|CustomWorkflowStep|CustomWorkflowOutput|CustomWorkflowLeaf'
  ```

  Expected for the first command: matches for `WorkflowTemplate` and added
  workflow `template` properties. Expected for the second command: no output;
  `rg` exits `1` when there are no matches, and that is the passing result for
  the forbidden-field check.

- [ ] Run the hard branch-contamination check:

  ```bash
  git diff origin/main...HEAD -- fern/openapi.yml fern/pages | \
    rg 'customSteps|outputRoutes|leafFields|requiredTemplateKeys|CustomWorkflowStep|CustomWorkflowOutput|CustomWorkflowLeaf'
  ```

  Expected: no output. `rg` exits `1` when there are no matches; that is the
  passing result for this check. If this prints matches, stop and move the
  template-only work to a clean branch from `origin/main`.

### Task 2.2: Validate Fern Contract

- [ ] Run:

  ```bash
  fern check
  ```

  Expected: pass.

- [ ] Run the available local generation smoke check:

  ```bash
  fern generate --group python-sdk --local --version 3.6.4 --no-require-env-vars --no-prompt
  fern generate --group ts-sdk --local --no-require-env-vars --no-prompt
  ```

  Expected: generation completes without schema errors. If local Python
  generation cannot run without publish credentials in the current environment,
  record the exact blocker and do not treat the TypeScript smoke as proof that
  Python SDK generation is safe.

### Task 2.3: Docs Timing

- [ ] Before generated Python SDK support exists, do not publish Python SDK
      examples that call `client.workflows.create(..., template=...)`.

- [ ] If docs must change in the Fern contract PR before Python SDK
      regeneration, limit them to the REST/OpenAPI JSON shape or generated API
      reference text:

  ```json
  {
    "name": "statement extraction",
    "extract": {
      "statement": {
        "fields": {}
      }
    },
    "template": {
      "statement_hint": "Prefer normalized values from the account summary."
    }
  }
  ```

- [ ] Do not document custom steps, output routes, leaf fields, or the future
      convenience methods in this template-only PR.

### Task 2.4: Fern Review And Publish

- [ ] Adversarial review checkpoint:
  - Is the public contract template-only?
  - Does `git diff origin/main...HEAD` exclude the larger custom-step OpenSpec,
    schema, and docs changes?
  - Does naming generate readable SDK types?
  - Do docs avoid promising unpublished Python SDK behavior?
  - Is publish order clear?

- [ ] Merge/publish Fern through the approved release path.

## Phase 3: groundx-python After Fern Publishes

**Repo:** `/Users/benjaminfletcher/git/groundx-python`

**Start condition:** Fern has published the workflow-template contract update.

**Files expected to change after regeneration:**

- Generated: `src/groundx/workflows/client.py`
- Generated: `src/groundx/workflows/raw_client.py`
- Generated: `src/groundx/types/workflow_request.py`
- Generated: `src/groundx/types/workflow_detail.py`
- Generated or new: `src/groundx/types/workflow_template.py`
- Generated: `src/groundx/types/__init__.py`
- Modify if needed before adding tests: `.fernignore`
- Hand-written tests: `tests/custom/test_client.py` or a focused
  `tests/custom/test_workflow_template.py`

### Task 3.1: Protect Hand-Written SDK Tests

- [ ] Before adding tests under `tests/custom`, inspect `.fernignore`.

- [ ] If `.fernignore` does not already protect `tests/custom`, add:

  ```text
  tests/custom
  ```

- [ ] Do not add new hand-written tests under an unprotected path.

### Task 3.2: Regenerate From Published Fern Contract

- [ ] Pull the generated SDK update from the approved Fern publish path.

- [ ] Confirm generated files expose `template` and were not hand-edited:

  ```bash
  rg -n 'template|WorkflowTemplate' \
    src/groundx/workflows/client.py \
    src/groundx/workflows/raw_client.py \
    src/groundx/types/workflow_request.py \
    src/groundx/types/workflow_detail.py \
    src/groundx/types/__init__.py
  ```

  Expected: generated create/update request surfaces and workflow detail model
  include `template`.

- [ ] Do not count Pydantic `extra="allow"` behavior as proof of support.
      Confirm `template` is a declared generated field on both request and
      detail models, and that any generated `WorkflowTemplate` type is imported
      through `src/groundx/types/__init__.py` if Fern creates a named class.

### Task 3.3: Add SDK Serialization Tests

- [ ] Add focused generated-client tests proving:
  - `client.workflows.create(..., template={"key": "value"})` serializes
    `template` into the request body.
  - `client.workflows.update(..., template={"key": "value"})` serializes
    `template` into the request body.
  - workflow detail responses deserialize `template` as a declared generated
    field, not only as an allowed extra.

- [ ] Add a typed-field assertion like this to the readback test:

  ```python
  from groundx.types import WorkflowDetail, WorkflowRequest

  def _model_fields(model: type) -> dict:
      return getattr(model, "model_fields", getattr(model, "__fields__", {}))

  assert "template" in _model_fields(WorkflowRequest)
  assert "template" in _model_fields(WorkflowDetail)
  ```

- [ ] Run:

  ```bash
  poetry run pytest -rP tests/custom -q
  poetry run mypy .
  ```

  Expected: pass.

### Task 3.4: Update Python SDK Docs After SDK Support Exists

- [ ] After generated `groundx-python` support is available, update Fern/public
      docs to show Python SDK usage:

  ```python
  workflow_response = client.workflows.create(
      name="statement extraction",
      extract=workflow_extract,
      template={
          "statement_hint": "Prefer normalized values from the account summary.",
      },
  )
  ```

- [ ] Run the relevant Fern docs preview/generation check after docs are
      updated.

### Task 3.5: SDK Review

- [ ] Adversarial review checkpoint:
  - Did generated changes come from Fern?
  - Are there no handwritten generated-file edits?
  - Do tests cover create, update, and readback?
  - Does readback prove a declared generated `template` field instead of
    relying on Pydantic extras?
  - Are new hand-written tests protected by `.fernignore`?
  - Is this still independent from extraction workflow convenience methods?
  - Were Python docs held until generated SDK support existed?

## Phase 4: Optional groundx-studio-harness YAML Passthrough

**Repo:** `/Users/benjaminfletcher/git/groundx-studio-harness`

**Start condition:** Approved only if the immediate feature must support
authored harness YAML configs, not just API/SDK callers. Deploy support also
requires a generated SDK version whose workflow create/update methods accept
`template`; before that, harness work must be compile-only or must fail clearly
when deploy sees `workflow.template`.

**Files:**

- Modify: `skills/groundx-extraction-workflows/templates/prompt.yaml`
- Modify: `skills/groundx-extraction-workflows/templates/compile_workflow.py`
- Modify: `skills/groundx-extraction-workflows/templates/deploy_workflow.py`
- Test: `skills/groundx-extraction-workflows/templates/test_compile_workflow.py`
- Test or modify if present:
  `scripts/tests/test-groundx-extraction-workflows.mjs`
- Modify references only if they teach the new YAML field:
  `skills/groundx-extraction-workflows/references/4_sdk_integration.md`,
  `skills/groundx-extraction-workflows/references/deploy.md`, and
  `skills/groundx-extraction-workflows/references/README.public.md`

### Task 4.1: Define Harness YAML Shape

- [ ] Support this authored YAML shape:

  ```yaml
  workflow:
    template:
      statement_hint: Prefer normalized account summary values.

  statement:
    fields:
      account_number:
        prompt:
          description: Account number.
          type: str
  ```

- [ ] The compiler must remove the top-level `workflow` metadata from the
      executable `extract` config when needed, but preserve `workflow.template`
      as top-level workflow settings.

### Task 4.2: Compile And Deploy Passthrough

- [ ] Update `compile_workflow.py` so `build_workflow_artifacts(...)` includes
      top-level `workflow["template"]` when authored YAML includes
      `workflow.template`.

- [ ] Update `deploy_workflow.py` so `_create_or_update_workflow(...)` checks
      whether the installed SDK workflow create/update methods accept
      `template` before deploying a workflow that includes top-level
      `workflow["template"]`.

- [ ] If `workflow["template"]` is present and the installed SDK does not
      support `template`, raise a clear `SystemExit` before making the workflow
      API call. Do not silently drop template values.

- [ ] If the installed SDK supports `template`, pass
      `template=workflow.get("template")` to both generated workflow create and
      update calls.

- [ ] Do not add custom-step metadata handling in this harness slice.

### Task 4.3: Harness Verification

- [ ] Add `test_compile_workflow.py` coverage proving:
      - `workflow.template` appears in compiled workflow JSON.
      - `workflow.template` does not remain incorrectly inside executable
        extract groups.
      - deploy passes template to a fake SDK that supports the argument.
      - deploy fails clearly before the API call with a fake older SDK that
        does not support the argument.
      - deploy without template still works with the fake older SDK.

- [ ] Run:

  ```bash
  cd /Users/benjaminfletcher/git/groundx-studio-harness
  python -m pytest skills/groundx-extraction-workflows/templates/test_compile_workflow.py -q
  node scripts/tests/test-groundx-extraction-workflows.mjs
  node scripts/validate.mjs
  ```

  Expected: pass.

- [ ] If plugin mirrors are generated by this change, refresh them only through
      the repo-approved sync command. Do not manually edit generated `plugins/`
      mirrors.

## Phase 5: Closeout

- [ ] Confirm repo status for each touched repo.
- [ ] Record exact verification commands and results.
- [ ] Summarize shipped repos:
  - `cashbot-go`: backend OpenAPI/runtime contract.
  - `eyelevel-fern-config`: public Fern/OpenAPI and docs.
  - `groundx-python`: deferred until Fern publish, then generated SDK/tests.
  - `groundx-studio-harness`: optional YAML passthrough only if approved.
- [ ] Return to the larger custom workflow/convenience-method plan only after
      this template-only plan is merged, published, or explicitly paused.
