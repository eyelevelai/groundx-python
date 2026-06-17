## 1. Fern Regen — Produce Generated Types and Client

- [x] 1.1 Trigger the Fern regen `workflow_dispatch` for `groundx-python` against the FINALIZED `eyelevel-fern-config` spec (commit 1280636) to produce `WorkflowTemplate`, the `template` field on `WorkflowRequest` and `WorkflowDetail`, and the updated workflow client methods
    TDD N/A: Fern regen workflow_dispatch cannot be triggered; reconciled generated files manually to match FINALIZED contract — same outcome as what regen would produce.
- [x] 1.2 Confirm `src/groundx/types/workflow_template.py` exists (or `WorkflowTemplate = typing.Dict[str, str]` appears in `src/groundx/types/`) after regen
- [x] 1.3 Confirm `WorkflowTemplate` is re-exported from `src/groundx/types/__init__.py` and importable as `from groundx.types import WorkflowTemplate`
- [x] 1.4 Confirm `template: typing.Optional[WorkflowTemplate]` appears on `WorkflowRequest` in `src/groundx/types/workflow_request.py`
- [x] 1.5 Confirm `template: typing.Optional[WorkflowTemplate]` appears on `WorkflowDetail` in `src/groundx/types/workflow_detail.py`
- [x] 1.6 Confirm `template` keyword argument is present on `WorkflowsClient.create(...)` and `WorkflowsClient.update(...)` in `src/groundx/workflows/client.py` (sync and async)

## 2. Hand-Written Tests — `tests/custom/`

- [x] 2.1 Create `tests/custom/test_workflow_template.py` with a test verifying `WorkflowTemplate` is importable as `from groundx.types import WorkflowTemplate` and equals `typing.Dict[str, str]`
- [x] 2.2 Add a test asserting `WorkflowRequest(template={"lang": "en"})` serializes the `template` field into the JSON body as `{"lang": "en"}` at the top level (use Pydantic `.model_dump(by_alias=True)` / `.dict()`)
- [x] 2.3 Add a test asserting `WorkflowRequest()` (no `template`) serializes with `template` absent from the JSON body (or `None` excluded on serialization)
- [x] 2.4 Add a test asserting `WorkflowRequest(template=None)` serializes with `template` absent from the JSON body
- [x] 2.5 Add a test asserting `WorkflowDetail` deserialization from a response dict containing `"template": {"prompt_lang": "en"}` yields `workflow_detail.template == {"prompt_lang": "en"}`
- [x] 2.6 Add a test asserting `WorkflowDetail` deserialization from a response dict that omits `"template"` yields `workflow_detail.template is None` without raising `AttributeError`
- [x] 2.7 Add a test asserting `WorkflowDetail` deserialization succeeds when the response dict contains an unknown field not in the current model (tolerant-reader / `extra="allow"` confirmation)
- [x] 2.8 Add a test asserting `WorkflowDetail` deserialization from a response dict containing `"template": {"tone": "formal"}` via a simulated `update` response yields `response.workflow.template == {"tone": "formal"}` (covers update response path; use `WorkflowResponse` if that is the return type of `update`)

## 3. README Update

- [x] 3.1 Add a "Workflow Template" subsection to `README.md` showing a `client.workflows.create(template={"key": "value"})` example with a `dict[str, str]` value; clarify that the field is optional and that omitting it leaves the template unset
- [x] 3.2 Add a companion `client.workflows.update(id="wf-id", template={"tone": "neutral"})` example showing per-key overlay semantics (omitting `template` preserves existing stored keys)

## 4. CI Verification

- [x] 4.1 Run `poetry run mypy .` and confirm exit code 0 with no errors referencing `WorkflowTemplate`, `WorkflowRequest.template`, or `WorkflowDetail.template`
- [x] 4.2 Run `poetry run pytest -rP -n auto .` and confirm exit code 0 with no failures referencing `template` fields on workflow types
- [x] 4.3 Run `openspec validate --type change "age-149-expose-workflow-template-config-through-the-public-workflow"` and confirm it passes

---

Consumer dependency note: `internal-arcadia-agents` imports `groundx[extract]>=3.4.3` — this change is additive and the `extract` submodule is untouched; no pin bump required. `groundx-on-prem` soft-binds via the `eyelevel/extract` image; no impact.

See workspace `openspec/changes/age-149-expose-workflow-template-config-through-the-public-workflow/tasks.md` for cross-service coordination and deferred items.
