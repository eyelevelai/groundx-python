# Extraction Workflow Definition Methods Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILLS: Use
> `superpowers:test-driven-development` for each code task and
> `superpowers:verification-before-completion` before claiming completion.
> Historical recipe steps use checkbox (`- [ ]`) syntax. Use `tasks.md` for
> current completion status and blockers.

## Current Status

The authoritative current status lives in `tasks.md`. The detailed phase
checklist below is retained as the original execution recipe, not as the current
completion tracker.

As of 2026-06-14:

- Local SDK, Fern docs, harness, Arcadia, and ADP scan work is implemented.
- Detached ADP support worktree was removed after scan-only verification.
- Post-review API correction is in progress: common create/update examples are
  path-first, and `load_extraction_definition(...)` is the promoted loader for
  inspection/reuse/copy workflows.
- Remaining gates are SDK publish, fresh published-package verification, and
  draft-only downstream docs/harness merge gates.

**Goal:** Give humans and automation first-class SDK operations to create or
update extraction workflows directly from YAML, load an extraction definition
from YAML or an existing workflow ID when inspection/reuse is needed, and keep
explicit source-specific loader aliases for advanced callers.

**Architecture:** Add an SDK-owned `ExtractionDefinition` object in the
hand-written extract surface. Client methods load definitions from YAML or
workflow responses, then create/update methods assemble generated workflow API
kwargs internally and delegate to the existing generated workflow client.

**Tech Stack:** Python SDK, Fern-generated workflow client surfaces, PyYAML,
pytest, mypy/pyright where configured, Fern docs, harness Node/Python scanners.

---

## Ground Rules

- Do not edit generated Fern files by hand.
- Do not rename OpenAPI schemas in this convenience-method change.
- Do not remove or change `prepare_extraction_yaml(...)`,
  `PreparedExtractionYaml`, `load_from_yaml(...)`, or `load_from_mapping(...)`.
- Do not make base SDK imports depend on the optional `extract` extra. The
  exported client module must lazy-import extraction helpers inside extraction
  methods and raise an actionable `pip install groundx[extract]` hint when the
  extra is missing.
- Do not promote kwargs-assembly helpers as a public technique. If needed, keep
  them private/internal, for example `_workflow_kwargs_from_extraction_definition(...)`.
- Do not remove harness `workflow_sdk_kwargs(...)` until the helper methods
  exist in a released minimum SDK version and fallback removal is separately
  approved.
- Do not touch dirty unrelated worktrees.
- Run an adversarial review after each repo checkpoint.
- Publishing and downstream dependency bumps remain blocked by the existing
  custom-step deployed-path e2e blocker.
- If GroundX Studio Harness web UI, publish, scaffold, or onboarding docs are
  touched, preserve the product invariant that the base experience is an
  authenticated app shell and onboarding is a configurable overlay/app metadata
  flow.

## Phase 0: OpenSpec Baseline

**Files:**

- Create:
  `/Users/benjaminfletcher/git/groundx-python/openspec/changes/add-extraction-workflow-convenience-methods/proposal.md`
- Create:
  `/Users/benjaminfletcher/git/groundx-python/openspec/changes/add-extraction-workflow-convenience-methods/design.md`
- Create:
  `/Users/benjaminfletcher/git/groundx-python/openspec/changes/add-extraction-workflow-convenience-methods/tasks.md`
- Create:
  `/Users/benjaminfletcher/git/groundx-python/openspec/changes/add-extraction-workflow-convenience-methods/execution-plan.md`
- Create:
  `/Users/benjaminfletcher/git/groundx-python/openspec/changes/add-extraction-workflow-convenience-methods/specs/extraction-workflow-convenience/spec.md`

- [x] Run:

  ```bash
  OPENSPEC_TELEMETRY=0 npx @fission-ai/openspec@1.3.1 validate add-extraction-workflow-convenience-methods --strict
  ```

  Expected: `Change 'add-extraction-workflow-convenience-methods' is valid`.

- [ ] Commit or leave the planning files staged according to the user's
      requested workflow.

## Phase 0.5: Refresh Implementation Branches

**Why:** The implementation worktrees were created before the workflow-template
closeout work was merged. Starting from stale branches can reintroduce old docs,
miss `.fernignore` protections, or hide conflicts until PR time.

- [ ] Refresh the SDK implementation branch:

  ```bash
  cd /Users/benjaminfletcher/git/groundx-python-support-custom-workflow-steps-sdk
  git fetch origin --prune
  git status --short --branch
  test -z "$(git status --porcelain)" || { git status --short; echo "worktree dirty; stop before rebase"; exit 1; }
  git rebase origin/main
  poetry run pytest tests/extract/prompt/test_persisted_workflow_extract.py -q
  git diff --check
  ```

  Expected: branch is based on current `origin/main`, existing custom-step work
  still passes its narrow extraction YAML gate, and only intended branch changes
  remain.

- [ ] Refresh the Fern docs branch:

  ```bash
  cd /Users/benjaminfletcher/git/eyelevel-fern-config
  git fetch origin --prune
  git status --short --branch
  test -z "$(git status --porcelain)" || { git status --short; echo "worktree dirty; stop before rebase"; exit 1; }
  git rebase origin/main
  fern check
  git diff --check
  ```

  Expected: branch includes the merged workflow-template docs closeout before
  the convenience-method docs edits start.

- [ ] Refresh the GroundX Studio Harness branch:

  ```bash
  cd /Users/benjaminfletcher/git/groundx-studio-harness-support-custom-workflow-steps
  git fetch origin --prune
  git status --short --branch
  test -z "$(git status --porcelain)" || { git status --short; echo "worktree dirty; stop before rebase"; exit 1; }
  git rebase origin/main
  python -m pytest skills/groundx-extraction-workflows/templates/test_compile_workflow.py -q
  node scripts/validate.mjs
  git diff --check
  ```

  Expected: branch includes the merged workflow-template closeout and the
  current plugin validation baseline before helper-preference edits start.

- [ ] Refresh the Arcadia branch before Phase 4 edits:

  ```bash
  cd /Users/benjaminfletcher/git/internal-arcadia-agents
  git fetch origin --prune
  git status --short --branch
  test -z "$(git status --porcelain)" || { git status --short; echo "worktree dirty; stop before rebase"; exit 1; }
  UPSTREAM="$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null)" || { echo "no upstream configured; stop and ask for target branch"; exit 1; }
  git rebase "$UPSTREAM"
  pytest prompts/test_arcadia_manager.py -q
  git diff --check
  ```

  Expected: Arcadia is clean, current with its configured upstream, and the
  prompt-manager baseline passes before helper-equivalence tests are added.

- [x] Close the detached ADP support worktree before Phase 5 edits:

  ```bash
  git -C /Users/benjaminfletcher/git/adp-poc worktree list --porcelain
  test ! -e /Users/benjaminfletcher/git/adp-poc-support-custom-workflow-steps
  ```

  Expected: detached ADP support worktree is removed if it has no local work.
  ADP scan work continues only in `/Users/benjaminfletcher/git/adp-poc`.

- [ ] If any rebase conflicts, stop in that worktree, resolve only the conflict,
      rerun that branch's narrow gate, and record the conflict resolution before
      continuing to Phase 1.
- [ ] If any worktree is dirty, stop before rebasing. Identify whether the dirty
      files are user work, generated output, or previous plan work, then ask for
      direction before stashing, committing, or editing those files.

## Phase 1: groundx-python SDK

**Repo:** `/Users/benjaminfletcher/git/groundx-python-support-custom-workflow-steps-sdk`

**Files:**

- Create: `src/groundx/extract/workflows.py`
- Modify: `src/groundx/extract/__init__.py`
- Modify: `src/groundx/ingest.py`
- Modify: `.fernignore`
- Modify: `README.md`
- Test: `tests/extract/test_extraction_workflow_definitions.py`
- Test: `tests/extract/test_import_boundaries.py`
- Test: `tests/custom/test_extraction_workflow_client_exports.py`

### Task 1: Add Failing Definition Loader Tests

- [ ] Create `tests/extract/test_extraction_workflow_definitions.py` with tests
      for the high-level API:

  ```python
  from pathlib import Path

  import pytest

  from groundx.extract import ExtractionDefinition, prepare_extraction_yaml


  CUSTOM_WORKFLOW_YAML = """
  workflow:
    template:
      "{{LANGUAGE}}": English
      "{{LANGUAGE_UNKNOWN}}": ""
      BILLING_HINT: Prefer line-item table values.
    custom_steps:
      - name: line_item_labels
        level: chunk
        kind: keys
        required_template_keys:
          - "{{LANGUAGE}}"
          - "{{LANGUAGE_UNKNOWN}}"
          - BILLING_HINT
  invoice:
    fields:
      invoice_number:
        prompt:
          description: Invoice number.
          type: str
  line_items:
    workflow_step: line_item_labels
    fields:
      description:
        workflow_output_key: label
        prompt:
          description: Line item description.
          type: str
  """


  def test_load_extraction_definition_from_yaml_path(tmp_path: Path) -> None:
      from groundx import GroundX

      yaml_path = tmp_path / "statement.yaml"
      yaml_path.write_text(CUSTOM_WORKFLOW_YAML, encoding="utf-8")
      client = GroundX(api_key="test")

      definition = client.load_extraction_definition_from_yaml(path=yaml_path)

      assert isinstance(definition, ExtractionDefinition)
      assert definition.extract["workflow"]["template"]["BILLING_HINT"]
      assert definition.custom_steps[0]["name"] == "line_item_labels"
      assert definition.output_routes
      assert definition.leaf_fields


  def test_load_extraction_definition_from_yaml_requires_one_source(
      tmp_path: Path,
  ) -> None:
      from groundx import GroundX

      yaml_path = tmp_path / "statement.yaml"
      yaml_path.write_text(CUSTOM_WORKFLOW_YAML, encoding="utf-8")
      client = GroundX(api_key="test")

      with pytest.raises(ValueError, match="exactly one"):
          client.load_extraction_definition_from_yaml()

      with pytest.raises(ValueError, match="exactly one"):
          client.load_extraction_definition_from_yaml(
              path=yaml_path,
              yaml_text=CUSTOM_WORKFLOW_YAML,
          )


  def test_load_extraction_definition_from_prepared() -> None:
      from groundx import GroundX

      client = GroundX(api_key="test")
      prepared = prepare_extraction_yaml(CUSTOM_WORKFLOW_YAML)

      definition = client.load_extraction_definition_from_yaml(prepared=prepared)

      assert definition.prepared == prepared
      assert definition.extract == prepared.persisted_workflow_extract


  def test_load_extraction_definition_from_authored_yaml_mapping() -> None:
      import yaml
      from groundx import GroundX

      client = GroundX(api_key="test")
      authored_mapping = yaml.safe_load(CUSTOM_WORKFLOW_YAML)

      definition = client.load_extraction_definition_from_yaml(
          mapping=authored_mapping,
      )

      assert definition.prepared is not None
      assert definition.template["{{LANGUAGE}}"] == "English"
      assert definition.template["{{LANGUAGE_UNKNOWN}}"] == ""


  def test_load_extraction_definition_from_persisted_extract_mapping_requires_explicit_kind() -> None:
      from groundx import GroundX

      client = GroundX(api_key="test")
      prepared = prepare_extraction_yaml(CUSTOM_WORKFLOW_YAML)

      definition = client.load_extraction_definition_from_yaml(
          mapping=prepared.persisted_workflow_extract,
          mapping_kind="workflow_extract",
      )

      assert definition.extract == prepared.persisted_workflow_extract
      assert definition.prepared is not None


  def test_load_extraction_definition_from_execution_extract_mapping_sets_prepared_none() -> None:
      from groundx import GroundX

      client = GroundX(api_key="test")
      execution_extract = {
          "invoice": {
              "fields": {
                  "invoice_number": {
                      "prompt": {
                          "description": "Invoice number.",
                          "type": "str",
                      }
                  }
              }
          }
      }

      definition = client.load_extraction_definition_from_yaml(
          mapping=execution_extract,
          mapping_kind="workflow_extract",
      )

      assert definition.extract == execution_extract
      assert definition.prepared is None


  def test_load_extraction_definition_rejects_non_string_template_values() -> None:
      import yaml
      from groundx import GroundX

      client = GroundX(api_key="test")
      authored_mapping = yaml.safe_load(CUSTOM_WORKFLOW_YAML)
      authored_mapping["workflow"]["template"]["{{LANGUAGE}}"] = 123

      with pytest.raises(ValueError, match="{{LANGUAGE}}"):
          client.load_extraction_definition_from_yaml(mapping=authored_mapping)
  ```

- [ ] Add tests for loading from a workflow ID:

  ```python
  from groundx.types.workflow_detail import WorkflowDetail
  from groundx.types.workflow_response import WorkflowResponse


  class FakeWorkflows:
      def __init__(self, response):
          self.response = response
          self.requested_id = None

      def get(self, id):
          self.requested_id = id
          return self.response


  def test_load_extraction_definition_from_workflow_id() -> None:
      from groundx import GroundX

      prepared = prepare_extraction_yaml(CUSTOM_WORKFLOW_YAML)
      client = GroundX(api_key="test")
      client._workflows = FakeWorkflows(
          {"workflow": {"workflow_id": "wf-1", "extract": prepared.persisted_workflow_extract}}
      )

      definition = client.load_extraction_definition_from_workflow("wf-1")

      assert client.workflows.requested_id == "wf-1"
      assert definition.extract == prepared.persisted_workflow_extract
      assert definition.custom_steps[0]["name"] == "line_item_labels"


  def test_load_extraction_definition_from_generated_workflow_response_preserves_top_level_settings() -> None:
      from groundx import GroundX

      prepared = prepare_extraction_yaml(CUSTOM_WORKFLOW_YAML)
      response = WorkflowResponse(
          workflow=WorkflowDetail(
              workflow_id="wf-1",
              extract=prepared.persisted_workflow_extract,
              template={"BILLING_HINT": "Prefer top-level template."},
              custom_steps=[
                  {
                      "name": "top_level_labels",
                      "level": "chunk",
                      "kind": "keys",
                      "required_template_keys": ["BILLING_HINT"],
                  }
              ],
              output_routes=prepared.persisted_workflow_extract["workflow"][
                  "output_routes"
              ],
              leaf_fields=prepared.persisted_workflow_extract["workflow"][
                  "leaf_fields"
              ],
              chunk_strategy="element",
          )
      )
      client = GroundX(api_key="test")
      client._workflows = FakeWorkflows(response)

      definition = client.load_extraction_definition_from_workflow("wf-1")

      assert definition.template == {"BILLING_HINT": "Prefer top-level template."}
      assert definition.custom_steps[0]["name"] == "top_level_labels"
      assert definition.output_routes
      assert definition.leaf_fields
      assert definition.chunk_strategy == "element"


  def test_load_extraction_definition_from_workflow_without_authored_metadata_sets_prepared_none() -> None:
      from groundx import GroundX

      execution_extract = {
          "invoice": {
              "fields": {
                  "invoice_number": {
                      "prompt": {
                          "description": "Invoice number.",
                          "type": "str",
                      }
                  }
              }
          }
      }
      client = GroundX(api_key="test")
      client._workflows = FakeWorkflows(
          WorkflowResponse(
              workflow=WorkflowDetail(workflow_id="wf-1", extract=execution_extract)
          )
      )

      definition = client.load_extraction_definition_from_workflow("wf-1")

      assert definition.extract == execution_extract
      assert definition.prepared is None


  def test_load_extraction_definition_from_workflow_requires_extract() -> None:
      from groundx import GroundX

      client = GroundX(api_key="test")
      client._workflows = FakeWorkflows({"workflow": {"workflow_id": "wf-1"}})

      with pytest.raises(Exception, match="wf-1"):
          client.load_extraction_definition_from_workflow("wf-1")
  ```

- [ ] Add concrete async loader parity tests. Use `asyncio.run(...)` so the
      tests do not depend on a pytest async plugin:

  ```python
  import asyncio


  class AsyncFakeWorkflows:
      def __init__(self, response):
          self.response = response
          self.requested_id = None

      async def get(self, id):
          self.requested_id = id
          return self.response


  def test_async_load_extraction_definition_from_yaml_text() -> None:
      from groundx import AsyncGroundX

      async def run() -> None:
          client = AsyncGroundX(api_key="test")

          definition = await client.load_extraction_definition_from_yaml(
              yaml_text=CUSTOM_WORKFLOW_YAML,
          )

          assert definition.prepared is not None
          assert definition.template["{{LANGUAGE}}"] == "English"
          assert definition.template["{{LANGUAGE_UNKNOWN}}"] == ""

      asyncio.run(run())


  def test_async_load_extraction_definition_from_workflow_id() -> None:
      from groundx import AsyncGroundX

      async def run() -> None:
          prepared = prepare_extraction_yaml(CUSTOM_WORKFLOW_YAML)
          client = AsyncGroundX(api_key="test")
          client._workflows = AsyncFakeWorkflows(
              WorkflowResponse(
                  workflow=WorkflowDetail(
                      workflow_id="wf-1",
                      extract=prepared.persisted_workflow_extract,
                  )
              )
          )

          definition = await client.load_extraction_definition_from_workflow("wf-1")

          assert client.workflows.requested_id == "wf-1"
          assert definition.extract == prepared.persisted_workflow_extract
          assert definition.custom_steps[0]["name"] == "line_item_labels"

      asyncio.run(run())


  def test_async_load_extraction_definition_requires_one_source() -> None:
      from groundx import AsyncGroundX

      async def run() -> None:
          client = AsyncGroundX(api_key="test")

          with pytest.raises(ValueError, match="exactly one"):
              await client.load_extraction_definition_from_yaml()

          with pytest.raises(ValueError, match="exactly one"):
              await client.load_extraction_definition_from_yaml(
                  yaml_text=CUSTOM_WORKFLOW_YAML,
                  prepared=prepare_extraction_yaml(CUSTOM_WORKFLOW_YAML),
              )

      asyncio.run(run())
  ```

- [ ] Run:

  ```bash
  poetry run pytest tests/extract/test_extraction_workflow_definitions.py -q
  ```

  Expected before implementation: import or attribute failures for
  `ExtractionDefinition` and loader methods.

- [ ] Create `tests/custom/test_extraction_workflow_client_exports.py` with
      import-boundary tests for the exported SDK client:

  Before creating this file, update `.fernignore` to protect the hand-written
  custom-test surface:

  ```text
  tests/custom
  ```

  Verify the entry exists with:

  ```bash
  rg -n "^tests/custom$" .fernignore
  ```

  This is required because `.fernignore` is the SDK's hand-written boundary,
  and the test must survive Fern regeneration.

  ```python
  import builtins
  import subprocess
  import sys
  import textwrap


  def _run_script(script: str) -> subprocess.CompletedProcess[str]:
      return subprocess.run(
          [sys.executable, "-c", textwrap.dedent(script).strip()],
          text=True,
          capture_output=True,
          check=False,
      )


  def test_base_groundx_import_does_not_import_extract_module() -> None:
      result = _run_script(
          """
          import builtins
          import sys

          extract_optional_roots = {
              "boto3",
              "celery",
              "dateparser",
              "fastapi",
              "google",
              "googleapiclient",
              "gspread",
              "minio",
              "openai",
              "PIL",
              "redis",
              "smolagents",
              "yaml",
          }

          original_import = builtins.__import__

          def guarded_import(name, *args, **kwargs):
              root = name.split(".", 1)[0]
              if name.startswith("groundx.extract") or root in extract_optional_roots:
                  raise AssertionError(
                      f"base SDK import must not import optional extract dependency {name}"
                  )
              return original_import(name, *args, **kwargs)

          builtins.__import__ = guarded_import

          import groundx
          from groundx import AsyncGroundX, GroundX

          assert GroundX
          assert AsyncGroundX
          assert "groundx.extract" not in sys.modules
          assert not (extract_optional_roots & set(sys.modules))
          """
      )

      assert result.returncode == 0, result.stderr


  def test_extraction_methods_without_extract_extra_raise_install_hint() -> None:
      result = _run_script(
          """
          import builtins

          extract_optional_roots = {
              "boto3",
              "celery",
              "dateparser",
              "fastapi",
              "google",
              "googleapiclient",
              "gspread",
              "minio",
              "openai",
              "PIL",
              "redis",
              "smolagents",
              "yaml",
          }

          original_import = builtins.__import__

          def guarded_import(name, *args, **kwargs):
              root = name.split(".", 1)[0]
              if name.startswith("groundx.extract") or root in extract_optional_roots:
                  raise ImportError("No module named yaml")
              return original_import(name, *args, **kwargs)

          builtins.__import__ = guarded_import

          from groundx import GroundX

          client = GroundX(api_key="test")
          try:
              client.load_extraction_definition_from_yaml(path="statement.yaml")
          except ImportError as exc:
              assert "groundx[extract]" in str(exc)
          else:
              raise AssertionError("expected missing extract extra hint")
          """
      )

      assert result.returncode == 0, result.stderr
  ```

  The subprocess wrapper is intentional: it prevents previous tests from hiding
  a module-time `groundx.extract` import through `sys.modules` cache state.

- [ ] Run:

  ```bash
  poetry run pytest tests/custom/test_extraction_workflow_client_exports.py -q
  ```

  Expected before implementation: the first test should pass only if the base
  client import is already clean; the second should fail until the lazy import
  wrapper raises the install hint.

### Task 2: Implement ExtractionDefinition And Loaders

- [ ] Create `src/groundx/extract/workflows.py` with:

  - `ExtractionDefinition` dataclass.
  - `_definition_from_prepared(prepared: PreparedExtractionYaml)`.
  - `_definition_from_workflow_detail(workflow: Any)`.
  - `_definition_from_extract_mapping(mapping: Mapping[str, Any])`.
  - `_load_definition_from_one_source(path=..., yaml_text=..., mapping=..., mapping_kind="authored_yaml", prepared=...)`.

- [ ] Implement source validation:

  ```python
  selected = [
      name
      for name, value in {
          "path": path,
          "yaml_text": yaml_text,
          "mapping": mapping,
          "prepared": prepared,
      }.items()
      if value is not None
  ]
  if len(selected) != 1:
      raise ValueError(
          "provide exactly one extraction definition source: "
          "path, yaml_text, mapping, or prepared"
      )
  ```

- [ ] Implement explicit mapping-kind validation:

  ```python
  allowed_mapping_kinds = {"authored_yaml", "workflow_extract"}
  if mapping_kind not in allowed_mapping_kinds:
      raise ValueError(
          "mapping_kind must be 'authored_yaml' or 'workflow_extract'"
      )
  if mapping is None and mapping_kind != "authored_yaml":
      raise ValueError("mapping_kind is only valid with mapping")
  if mapping is not None and mapping_kind == "workflow_extract":
      return _definition_from_extract_mapping(mapping)
  ```

  With `mapping_kind="authored_yaml"` or omitted, `mapping` must follow the
  same preparation path as `yaml_text`. Do not infer `workflow_extract` by
  inspecting dict keys; authored YAML and execution-only workflow extract
  mappings can be structurally identical.

- [ ] Export `ExtractionDefinition` from `src/groundx/extract/__init__.py`.

- [ ] Add `GroundX.load_extraction_definition_from_yaml(...)` in
      `src/groundx/ingest.py`. It should lazy-import the extract workflow
      module inside the method body, call the extract module loader, and return
      `ExtractionDefinition`.

- [ ] Add `GroundX.load_extraction_definition_from_workflow(...)` in
      `src/groundx/ingest.py`. It should lazy-import the extract workflow
      module, call `self.workflows.get(id=workflow_id)`, extract the generated
      response's `workflow`, and return `ExtractionDefinition`.

- [ ] Define `ExtractionDefinition.prepared` as optional. YAML-loaded
      definitions set it to the `PreparedExtractionYaml`. Workflow-loaded
      definitions set it only when the workflow extract can be round-tripped
      through `prepare_extraction_yaml(...)`, usually because
      `_groundx_persisted_extract` is present. Workflow-loaded definitions that
      only have execution groups and top-level workflow settings must set
      `prepared=None`.

- [ ] For workflow-loaded definitions, preserve generated `WorkflowDetail`
      top-level settings (`template`, `custom_steps`, `output_routes`,
      `leaf_fields`, `chunk_strategy`, `section_strategy`, and `steps`) ahead of
      fallback metadata under `extract["workflow"]`.

- [ ] Add a small lazy-import helper in `src/groundx/ingest.py`, for example
      `_import_extraction_workflows()`, that catches missing optional extract
      dependencies and raises an actionable `ImportError` mentioning
      `pip install groundx[extract]`. Do not import `groundx.extract` at module
      import time.

- [ ] Add async parity on `AsyncGroundX`. YAML loading can reuse the same local
      parser. Workflow-ID loading must await the generated workflow get call.

- [ ] Run:

  ```bash
  poetry run pytest tests/extract/test_extraction_workflow_definitions.py tests/custom/test_extraction_workflow_client_exports.py -q
  ```

  Expected: loader tests pass; create/update tests will be added next.

### Task 3: Add Failing Create/Update Tests

- [ ] Extend `tests/extract/test_extraction_workflow_definitions.py` with sync
      create/update forwarding tests:

  ```python
  class CreateUpdateWorkflows:
      def __init__(self) -> None:
          self.created = None
          self.updated = None

      def create(self, **kwargs):
          self.created = kwargs
          return {"workflow": {"workflow_id": "created"}}

      def update(self, id, **kwargs):
          self.updated = (id, kwargs)
          return {"workflow": {"workflow_id": id}}


  FIXED_STAGE_ATTRS = (
      "chunk_instruct",
      "chunk_keys",
      "chunk_summary",
      "doc_keys",
      "doc_summary",
      "sect_instruct",
      "sect_summary",
  )


  FIXED_STAGE_WIRE_KEYS = (
      "chunk-instruct",
      "chunk-keys",
      "chunk-summary",
      "doc-keys",
      "doc-summary",
      "sect-instruct",
      "sect-summary",
  )


  def _step_value(steps, attr):
      if isinstance(steps, dict):
          return steps.get(attr, steps.get(attr.replace("_", "-")))
      return getattr(steps, attr)


  def test_create_extraction_workflow_accepts_definition(tmp_path: Path) -> None:
      from groundx import GroundX

      yaml_path = tmp_path / "statement.yaml"
      yaml_path.write_text(CUSTOM_WORKFLOW_YAML, encoding="utf-8")
      client = GroundX(api_key="test")
      definition = client.load_extraction_definition_from_yaml(path=yaml_path)
      client._workflows = CreateUpdateWorkflows()
      request_options = {"timeout_in_seconds": 30}

      response = client.create_extraction_workflow(
          definition=definition,
          name="statement extraction",
          request_options=request_options,
      )

      assert response == {"workflow": {"workflow_id": "created"}}
      assert client.workflows.created["request_options"] == request_options
      assert client.workflows.created["extract"]["workflow"]["custom_steps"]
      assert client.workflows.created["custom_steps"][0]["name"] == "line_item_labels"
      steps = client.workflows.created["steps"]
      for attr in FIXED_STAGE_ATTRS:
          assert _step_value(steps, attr) is None


  def test_update_extraction_workflow_accepts_definition(tmp_path: Path) -> None:
      from groundx import GroundX

      yaml_path = tmp_path / "statement.yaml"
      yaml_path.write_text(CUSTOM_WORKFLOW_YAML, encoding="utf-8")
      client = GroundX(api_key="test")
      definition = client.load_extraction_definition_from_yaml(path=yaml_path)
      client._workflows = CreateUpdateWorkflows()
      request_options = {"timeout_in_seconds": 31}

      response = client.update_extraction_workflow(
          "wf-1",
          definition=definition,
          name="statement extraction",
          request_options=request_options,
      )

      assert response == {"workflow": {"workflow_id": "wf-1"}}
      assert client.workflows.updated[0] == "wf-1"
      assert client.workflows.updated[1]["request_options"] == request_options
      assert client.workflows.updated[1]["custom_steps"]
      steps = client.workflows.updated[1]["steps"]
      for attr in FIXED_STAGE_ATTRS:
          assert _step_value(steps, attr) is None


  LEGACY_YAML = """
  invoice:
    fields:
      invoice_number:
        prompt:
          description: Invoice number.
          type: str
  """


  def test_create_extraction_workflow_legacy_yaml_does_not_disable_fixed_defaults(
      tmp_path: Path,
  ) -> None:
      from groundx import GroundX

      yaml_path = tmp_path / "legacy.yaml"
      yaml_path.write_text(LEGACY_YAML, encoding="utf-8")
      client = GroundX(api_key="test")
      client._workflows = CreateUpdateWorkflows()

      client.create_extraction_workflow(
          path=yaml_path,
          name="statement extraction",
      )

      assert "steps" not in client.workflows.created
  ```

- [ ] Add source one-of tests for create/update:

  ```python
  def test_create_extraction_workflow_requires_exactly_one_source(tmp_path: Path) -> None:
      from groundx import GroundX

      yaml_path = tmp_path / "statement.yaml"
      yaml_path.write_text(CUSTOM_WORKFLOW_YAML, encoding="utf-8")
      client = GroundX(api_key="test")
      definition = client.load_extraction_definition_from_yaml(path=yaml_path)

      with pytest.raises(ValueError, match="exactly one"):
          client.create_extraction_workflow(name="statement extraction")

      with pytest.raises(ValueError, match="exactly one"):
          client.create_extraction_workflow(
              path=yaml_path,
              yaml_text=CUSTOM_WORKFLOW_YAML,
              name="statement extraction",
          )

      with pytest.raises(ValueError, match="exactly one"):
          client.create_extraction_workflow(
              definition=definition,
              path=yaml_path,
              name="statement extraction",
          )

      with pytest.raises(ValueError, match="mapping_kind"):
          client.create_extraction_workflow(
              definition=definition,
              mapping_kind="workflow_extract",
              name="statement extraction",
          )


  def test_update_extraction_workflow_requires_exactly_one_source(tmp_path: Path) -> None:
      from groundx import GroundX

      yaml_path = tmp_path / "statement.yaml"
      yaml_path.write_text(CUSTOM_WORKFLOW_YAML, encoding="utf-8")
      client = GroundX(api_key="test")
      definition = client.load_extraction_definition_from_yaml(path=yaml_path)

      with pytest.raises(ValueError, match="exactly one"):
          client.update_extraction_workflow("wf-1", name="statement extraction")

      with pytest.raises(ValueError, match="exactly one"):
          client.update_extraction_workflow(
              "wf-1",
              definition=definition,
              prepared=definition.prepared,
              name="statement extraction",
          )

      with pytest.raises(ValueError, match="mapping_kind"):
          client.update_extraction_workflow(
              "wf-1",
              definition=definition,
              mapping_kind="workflow_extract",
              name="statement extraction",
          )
  ```

- [ ] Add async create/update tests using async fake workflow clients:

  ```python
  class AsyncCreateUpdateWorkflows:
      def __init__(self) -> None:
          self.created = None
          self.updated = None

      async def create(self, **kwargs):
          self.created = kwargs
          return {"workflow": {"workflow_id": "created"}}

      async def update(self, id, **kwargs):
          self.updated = (id, kwargs)
          return {"workflow": {"workflow_id": id}}


  def test_async_create_and_update_extraction_workflow_accept_definition(
      tmp_path: Path,
  ) -> None:
      from groundx import AsyncGroundX

      async def run() -> None:
          yaml_path = tmp_path / "statement.yaml"
          yaml_path.write_text(CUSTOM_WORKFLOW_YAML, encoding="utf-8")
          client = AsyncGroundX(api_key="test")
          definition = await client.load_extraction_definition_from_yaml(
              path=yaml_path,
          )
          client._workflows = AsyncCreateUpdateWorkflows()
          create_request_options = {"timeout_in_seconds": 30}
          update_request_options = {"timeout_in_seconds": 31}

          create_response = await client.create_extraction_workflow(
              definition=definition,
              name="statement extraction",
              request_options=create_request_options,
          )
          update_response = await client.update_extraction_workflow(
              "wf-1",
              definition=definition,
              name="statement extraction",
              request_options=update_request_options,
          )

          assert create_response == {"workflow": {"workflow_id": "created"}}
          assert update_response == {"workflow": {"workflow_id": "wf-1"}}
          assert client.workflows.created["request_options"] == create_request_options
          assert client.workflows.updated[1]["request_options"] == update_request_options
          assert client.workflows.created["custom_steps"][0]["name"] == (
              "line_item_labels"
          )
          assert client.workflows.updated[1]["custom_steps"][0]["name"] == (
              "line_item_labels"
          )
          for attr in FIXED_STAGE_ATTRS:
              assert _step_value(client.workflows.created["steps"], attr) is None
              assert _step_value(client.workflows.updated[1]["steps"], attr) is None

      asyncio.run(run())


  def test_async_create_extraction_workflow_requires_exactly_one_source(
      tmp_path: Path,
  ) -> None:
      from groundx import AsyncGroundX

      async def run() -> None:
          yaml_path = tmp_path / "statement.yaml"
          yaml_path.write_text(CUSTOM_WORKFLOW_YAML, encoding="utf-8")
          client = AsyncGroundX(api_key="test")
          definition = await client.load_extraction_definition_from_yaml(
              path=yaml_path,
          )

          with pytest.raises(ValueError, match="exactly one"):
              await client.create_extraction_workflow(name="statement extraction")

          with pytest.raises(ValueError, match="exactly one"):
              await client.create_extraction_workflow(
                  definition=definition,
                  path=yaml_path,
                  name="statement extraction",
              )

      asyncio.run(run())
  ```

- [ ] Add generated workflow-client serialization tests that send the helper
      output through the real generated `WorkflowsClient`, using the existing
      recording-client pattern from `tests/custom/test_client.py`:

  ```python
  import typing

  from groundx.core.http_client import get_request_body
  from groundx.workflows.client import WorkflowsClient


  class _DummyWorkflowResponse:
      status_code = 200
      headers: typing.Dict[str, str] = {}
      text = ""

      def json(self) -> typing.Dict[str, typing.Any]:
          return {"workflow": {"workflowId": "created"}}


  class _RecordingHttpClient:
      def __init__(self) -> None:
          self.calls: typing.List[typing.Tuple[str, typing.Dict[str, typing.Any]]] = []

      def request(self, path: str, **kwargs: typing.Any) -> _DummyWorkflowResponse:
          json_body, data_body = get_request_body(
              json=kwargs.get("json"),
              data=kwargs.get("data"),
              request_options=kwargs.get("request_options"),
              omit=kwargs.get("omit"),
          )
          encoded_kwargs = dict(kwargs)
          encoded_kwargs["json"] = json_body
          encoded_kwargs["data"] = data_body
          self.calls.append((path, encoded_kwargs))
          return _DummyWorkflowResponse()


  class _RecordingWrapper:
      def __init__(self, http_client: _RecordingHttpClient) -> None:
          self.httpx_client = http_client


  def test_create_extraction_workflow_serializes_generated_wire_keys(
      tmp_path: Path,
  ) -> None:
      from groundx import GroundX

      yaml_path = tmp_path / "statement.yaml"
      yaml_path.write_text(CUSTOM_WORKFLOW_YAML, encoding="utf-8")
      http_client = _RecordingHttpClient()
      client = GroundX(api_key="test")
      client._workflows = WorkflowsClient(
          client_wrapper=typing.cast(typing.Any, _RecordingWrapper(http_client))
      )
      request_options = {"additional_headers": {"X-Test": "1"}}

      client.create_extraction_workflow(
          path=yaml_path,
          name="statement extraction",
          request_options=request_options,
      )

      assert http_client.calls[0][0] == "v1/workflow"
      assert http_client.calls[0][1]["method"] == "POST"
      assert http_client.calls[0][1]["request_options"] == request_options
      body = http_client.calls[0][1]["json"]
      assert body["customSteps"][0]["requiredTemplateKeys"] == [
          "{{LANGUAGE}}",
          "{{LANGUAGE_UNKNOWN}}",
          "BILLING_HINT",
      ]
      assert body["outputRoutes"][0]["workflowGroup"] == "line_items"
      assert body["leafFields"][0]["finalPath"] == "/line_items/*/description"
      for key in FIXED_STAGE_WIRE_KEYS:
          assert key in body["steps"]
          assert body["steps"][key] is None
      assert "search-query" not in body["steps"]
      assert "sect-keys" not in body["steps"]
      assert "custom_steps" not in body
      assert "output_routes" not in body
      assert "leaf_fields" not in body


  def test_update_extraction_workflow_serializes_generated_wire_keys(
      tmp_path: Path,
  ) -> None:
      from groundx import GroundX

      yaml_path = tmp_path / "statement.yaml"
      yaml_path.write_text(CUSTOM_WORKFLOW_YAML, encoding="utf-8")
      http_client = _RecordingHttpClient()
      client = GroundX(api_key="test")
      client._workflows = WorkflowsClient(
          client_wrapper=typing.cast(typing.Any, _RecordingWrapper(http_client))
      )
      request_options = {"timeout_in_seconds": 22}

      client.update_extraction_workflow(
          "wf-1",
          path=yaml_path,
          name="statement extraction",
          request_options=request_options,
      )

      assert http_client.calls[0][0] == "v1/workflow/wf-1"
      assert http_client.calls[0][1]["method"] == "PUT"
      assert http_client.calls[0][1]["request_options"] == request_options
      body = http_client.calls[0][1]["json"]
      assert body["customSteps"][0]["name"] == "line_item_labels"
      for key in FIXED_STAGE_WIRE_KEYS:
          assert key in body["steps"]
          assert body["steps"][key] is None
  ```

- [ ] Run:

  ```bash
  poetry run pytest tests/extract/test_extraction_workflow_definitions.py -q
  ```

  Expected before implementation: create/update method failures.

### Task 4: Implement Create/Update Methods

- [ ] Add private/internal kwargs assembly from `ExtractionDefinition`, for
      example `_workflow_kwargs_from_extraction_definition(...)`. Behavior:

  - copy `extract` from `definition.extract`;
  - copy `template`, `custom_steps`, `output_routes`, and `leaf_fields` when
    present;
  - include `name` when supplied;
  - default `chunk_strategy` to `"element"` for YAML-loaded definitions and omit
    it only when caller passes `None`;
  - preserve `definition.chunk_strategy` for workflow-loaded definitions when
    the caller does not override it;
  - include `section_strategy` when supplied or preserved from the definition;
  - include caller-supplied `steps` when supplied, otherwise preserve
    `definition.steps` when present;
  - if custom workflow steps exist and `steps` is omitted, include the same
    empty fixed-step overlay used by the harness custom-workflow path:
    `WorkflowSteps(chunk_instruct=None, chunk_keys=None, chunk_summary=None,
    doc_keys=None, doc_summary=None, sect_instruct=None, sect_summary=None)`.
    Do not add `search_query` or `sect_keys` to this overlay in this plan; the
    current harness compiler intentionally preserves the legacy seven-key wire
    shape;
  - keep this helper private/internal and absent from promoted docs.

- [ ] Add `GroundX.create_extraction_workflow(...)` in `src/groundx/ingest.py`.
      It should resolve exactly one source into `ExtractionDefinition`, assemble
      kwargs internally, pass optional `request_options`, and return
      `self.workflows.create(**kwargs)`.

- [ ] Add `GroundX.update_extraction_workflow(...)` in `src/groundx/ingest.py`.
      It should resolve exactly one source into `ExtractionDefinition`, assemble
      kwargs internally, pass optional `request_options`, and return
      `self.workflows.update(id, **kwargs)`.

- [ ] Use one shared source-selection helper for sync and async create/update.
      It must validate exactly one of `definition`, `path`, `yaml_text`,
      `mapping`, or `prepared`, and it must reject `mapping_kind` unless
      `mapping` is the selected source.

- [ ] Add equivalent async methods on `AsyncGroundX`:

  - `async def load_extraction_definition_from_yaml(...)` returns
    `ExtractionDefinition` and may call the same local parser as sync.
  - `async def load_extraction_definition_from_workflow(...)` awaits
    `self.workflows.get(id=workflow_id)`.
  - `async def create_extraction_workflow(...)` awaits
    `self.workflows.create(**kwargs)`.
  - `async def update_extraction_workflow(...)` awaits
    `self.workflows.update(id, **kwargs)`.

  Do not implement async methods as sync wrappers that call generated async
  workflow methods without `await`; the async tests above must fail if the
  generated async workflow client is not awaited.

- [ ] Add docstrings for all promoted client methods:

  - sync and async consolidated loaders;
  - sync and async YAML loader aliases;
  - sync and async workflow-ID loader aliases;
  - sync and async create helpers;
  - sync and async update helpers.

  Docstrings must include parameters, return values, sync examples, async
  examples where relevant, update semantics, and explicit workflow assignment
  after create. They must also state that extraction definition methods require
  `groundx[extract]`, while base SDK import and non-extraction calls do not.

- [ ] Update import-boundary tests so `from groundx.extract import
      ExtractionDefinition` works.

- [ ] Update `README.md` or the repo's hand-written SDK reference section so
      the promoted extraction workflow methods are listed beside `ingest` and
      `ingest_directories`.

- [ ] Run:

  ```bash
  poetry run pytest tests/extract/test_extraction_workflow_definitions.py tests/extract/test_import_boundaries.py -q
  poetry run pytest tests/custom/test_extraction_workflow_client_exports.py -q
  ```

  Expected: all convenience helper and import tests pass.

### Task 5: SDK Regression Gates

- [ ] Run:

  ```bash
  poetry run pytest tests/extract/prompt/test_manager.py tests/extract/prompt/test_persisted_workflow_extract.py -q
  poetry run pytest tests/custom/test_client.py -q
  poetry run pytest tests/custom/test_extraction_workflow_client_exports.py -q
  poetry run pytest tests/extract/test_extraction_workflow_definitions.py -q
  poetry run pytest -rP -n auto tests/custom tests/extract
  poetry run mypy .
  poetry install --extras extract --extras aiohttp
  poetry run pytest -rP -n auto -m aiohttp .
  git diff --check
  ```

  Expected: all pass. If `mypy` is not configured or fails for unrelated known
  issues, record exact output and run the narrow type gate that the repo uses for
  SDK closeout.

- [ ] Adversarial review:

  - Confirm generated files are untouched.
  - Confirm `import groundx` and `from groundx import GroundX, AsyncGroundX` do
    not import optional extract dependencies.
  - Confirm extraction definition methods fail with an actionable
    `groundx[extract]` install hint when extract dependencies are unavailable.
  - Confirm `prepare_extraction_yaml(...)` still returns `PreparedExtractionYaml`.
  - Confirm `load_from_yaml(...)` and `load_from_mapping(...)` still behave as
    low-level conversion helpers.
  - Confirm `mapping` defaults to authored YAML semantics and existing workflow
    `extract` mappings require `mapping_kind="workflow_extract"`.
  - Confirm template values are validated as strings, and `{{LANGUAGE}}` plus
    `{{LANGUAGE_UNKNOWN}}` placeholder keys survive exactly, including empty
    string values.
  - Confirm workflow-loaded definitions preserve generated `WorkflowDetail`
    top-level settings and use `prepared=None` when authored metadata is absent.
  - Confirm no promoted doc or example teaches a kwargs-prep helper.
  - Confirm helper-produced kwargs match generated `workflows.create/update`
    parameter names.
  - Confirm helper-produced kwargs serialize through the generated workflow
    client to public camelCase JSON names.
  - Confirm update sends full extraction settings and does not teach name-only
    update.
  - Confirm method docstrings and README/reference docs match the standard for
    hand-written SDK helpers.
  - Confirm custom workflow YAML disables the exact seven fixed defaults
    `chunk_instruct`, `chunk_keys`, `chunk_summary`, `doc_keys`, `doc_summary`,
    `sect_instruct`, and `sect_summary` by default, while legacy YAML does not.

## Phase 1.5: SDK Publish And Fresh-Install Gate

**Why:** Public docs and harness helper-preference changes should not merge
until the helper methods are available from a released Python SDK. Draft PRs are
allowed before this gate; public merge is not.

- [ ] Confirm the custom-step deployed-path blocker is resolved. The SDK
      implementation PR may be reviewed before this, but release and downstream
      dependency bumps remain blocked until custom workflow steps work on the
      deployed path.

- [ ] Merge the SDK implementation PR only after Phase 1 gates pass and the
      deployed-path blocker is resolved.

- [ ] Have a maintainer publish the Python SDK release through the repo's normal
      tag-based release flow.

- [ ] Verify the released package from a fresh environment:

  ```bash
  SMOKE_DIR="$(mktemp -d /tmp/groundx-extraction-workflow-methods.XXXXXX)"
  python -m venv "$SMOKE_DIR"
  "$SMOKE_DIR/bin/python" -m pip install --upgrade pip
  "$SMOKE_DIR/bin/python" -m pip install --upgrade "groundx[extract]"
  "$SMOKE_DIR/bin/python" - <<'PY'
  from groundx import AsyncGroundX, GroundX

  for client_cls in (GroundX, AsyncGroundX):
      for name in (
          "load_extraction_definition",
          "load_extraction_definition_from_yaml",
          "load_extraction_definition_from_workflow",
          "create_extraction_workflow",
          "update_extraction_workflow",
      ):
          assert callable(getattr(client_cls, name, None)), (client_cls, name)

  client = GroundX(api_key="test")
  definition = client.load_extraction_definition(
      yaml_text="""
  invoice:
    fields:
      invoice_number:
        prompt:
          description: Invoice number.
          type: str
  """
  )
  assert definition.extract
  assert definition.prepared is not None
  PY
  ```

  Expected: the latest published `groundx[extract]` exposes the promoted helper
  methods and can load authored YAML without a local checkout.

- [ ] Record the published SDK version in the OpenSpec closeout notes before
      merging public docs or harness helper-preference PRs.

## Phase 2: Public Docs

**Repo:** `/Users/benjaminfletcher/git/eyelevel-fern-config`

**Files:**

- Modify: `fern/pages/extract-data-from-documents.mdx`
- Modify any Fern docs navigation or SDK helper reference pages needed to make
  the methods discoverable like `ingest` and `ingest_directories`.
- Test/validate: repo docs checks and OpenSpec validation for any touched
  OpenSpec files.

- [ ] Before opening the docs PR, check Phase 1.5. If the SDK has not been
      published and verified from a fresh install, open the docs PR as draft and
      keep it draft-only until the gate is complete.

- [ ] Replace the manual workflow settings block with:

  ```python
  import os

  from groundx import GroundX

  client = GroundX(api_key=os.environ["GROUNDX_API_KEY"])

  workflow_response = client.create_extraction_workflow(
      path="statement.yaml",
      name="statement extraction",
  )

  workflow_id = workflow_response.workflow.workflow_id
  if workflow_id is None:
      raise RuntimeError("GroundX did not return a workflow ID")

  client.workflows.add_to_id(id=bucket_id, workflow_id=workflow_id)
  ```

- [ ] Add the matching update example:

  ```python
  client.update_extraction_workflow(
      workflow_id,
      path="statement.yaml",
      name="statement extraction",
  )
  ```

- [ ] Add the workflow-ID load example:

  ```python
  definition = client.load_extraction_definition(workflow_id=workflow_id)
  ```

- [ ] Keep an advanced note that `prepare_extraction_yaml(...)` returns
      `PreparedExtractionYaml` for callers that need final groups, workflow
      groups, route metadata, or custom metadata inspection from authored YAML.
      Also note that definitions loaded from an existing workflow may have
      `definition.prepared is None` when the workflow does not preserve authored
      YAML metadata.

- [ ] Add method-level public documentation for the promoted helper methods with
      signatures, accepted source arguments, return values, sync examples, async
      examples, update semantics, explicit `groundx[extract]` dependency
      guidance, and explicit workflow assignment after create.

- [ ] Do not change `fern/openapi.yml` schema names in this plan.

- [ ] Run the repo's docs validation commands, including:

  ```bash
  fern check
  git diff --check
  ```

  Expected: docs validate and no whitespace errors.

- [ ] Adversarial review:

  - Confirm docs no longer teach manual metadata copying as the primary path.
  - Confirm docs do not claim a released helper before the SDK release gate is
    satisfied.
  - Confirm docs keep explicit bucket/account assignment after workflow create.
  - Confirm docs explain `groundx[extract]` without implying the base SDK import
    requires extract dependencies.
  - Confirm docs do not imply workflow-loaded definitions always have authored
    YAML metadata.
  - Confirm the promoted helper methods are discoverable as first-class SDK
    helpers, not only mentioned inside one extraction walkthrough.
  - Confirm generated schema names remain untouched.

## Phase 3: Harness Templates And Skills

**Repo:** `/Users/benjaminfletcher/git/groundx-studio-harness-support-custom-workflow-steps`

**Files:**

- Modify: `skills/groundx-extraction-workflows/templates/deploy_workflow.py`
- Modify: `skills/groundx-extraction-workflows/templates/run_extraction.py`
- Modify: `skills/groundx-extraction-workflows/templates/batch_extraction.py`
- Modify: `skills/groundx-extraction-workflows/templates/prompt_manager.py`
- Modify: `skills/groundx-extraction-workflows/templates/compile_workflow.py`
- Modify: `skills/groundx-extraction-workflows/templates/test_compile_workflow.py`
- Modify: `scripts/tests/test-groundx-extraction-workflows.mjs`
- Modify: `scripts/tests/test-extraction-deploy-workflow.mjs`
- Modify: `skills/groundx-python/references/02-core-sdk.md`
- Modify as needed: `skills/groundx-python/evals/evals.json`
- Modify as needed: `skills/groundx-extraction-workflows/SKILL.md`
- Modify as needed: `skills/groundx-extraction-workflows/evals/evals.json`
- Modify architecture/API-surface references that enumerate hand-written Python
  SDK helpers, including `skills/groundx-architecture/references/api-surface.md`.
- Modify: `skills/groundx-extraction-workflows/references/public-docs.md`
- Modify references under `skills/groundx-extraction-workflows/references/`
- Modify scanner fixtures or expectations if existing checks encode the old
  manual workflow path.
- Modify routing/source manifests only if discoverability or first-entry
  ownership changes.
- Modify changelog/version surfaces if harness packaging rules require a
  version bump for changed plugin payload.
- Do not list or edit `plugins/` mirror files as source files. If source changes
  alter plugin payload, refresh mirrors with `node scripts/sync-plugin.mjs`,
  review the generated diff, rerun `node scripts/sync-plugin.mjs --check`, and
  rerun `node scripts/validate.mjs` after the generated-output refresh.

- [ ] Before opening the harness PR, check Phase 1.5. If the SDK has not been
      published and verified from a fresh install, open the harness PR as draft
      and keep it draft-only until the gate is complete. If the harness minimum
      supported SDK version is not bumped, the older-SDK fallback must remain
      covered by tests.

- [ ] Add compatibility detection:

  ```python
  def _client_has_extraction_workflow_helpers(gx: typing.Any) -> bool:
      return all(
          callable(getattr(gx, name, None))
          for name in (
              "load_extraction_definition_from_yaml",
              "load_extraction_definition",
              "create_extraction_workflow",
              "update_extraction_workflow",
          )
      )
  ```

- [ ] Keep deploy/run/batch compile steps in place before any API call:

  ```python
  workflow, extraction_metadata = build_workflow_artifacts(yaml_path, name=workflow_name)
  errors = validate_workflow(workflow)
  if errors:
      raise SystemExit("workflow validation failed:\n  - " + "\n  - ".join(errors))
  _write_workflow_artifacts(workflow, extraction_metadata)
  ```

  Existing helper-backed paths must still write `workflow.json` and
  `extraction_workflow_metadata_v1.json`. The helper methods may be used for the
  API call only after these artifacts are produced and validated.

- [ ] In create paths, prefer:

  ```python
  workflow, metadata = build_workflow_artifacts(yaml_path, workflow_name)
  _validate_and_write_artifacts(workflow, metadata)
  if _client_has_extraction_workflow_helpers(gx):
      response = gx.create_extraction_workflow(
          path=yaml_path,
          name=workflow_name,
      )
  else:
      response = gx.workflows.create(**workflow_sdk_kwargs(workflow))
  ```

- [ ] In update paths, prefer:

  ```python
  workflow, metadata = build_workflow_artifacts(yaml_path, workflow_name)
  _validate_and_write_artifacts(workflow, metadata)
  if _client_has_extraction_workflow_helpers(gx):
      response = gx.update_extraction_workflow(
          workflow_id,
          path=yaml_path,
          name=workflow_name,
      )
  else:
      response = gx.workflows.update(workflow_id, **workflow_sdk_kwargs(workflow))
  ```

- [ ] Keep `compile_workflow.py` building offline workflow JSON and
      `workflow_sdk_kwargs(...)` for fallback. Do not delete either in this
      plan.

- [ ] Update harness references so path-first create/update is preferred,
      definition loading is the reuse/inspection path, and
      `workflow_sdk_kwargs(...)` is compatibility/offline support.

- [ ] Update `skills/groundx-extraction-workflows/references/public-docs.md`:

  - replace the old primary flow that says to use
    `prepare_extraction_yaml(...)` and pass prepared workflow groups;
  - show the helper-backed public flow for creating and updating workflows
    directly from a YAML path;
  - allow method names such as
    `load_extraction_definition(...)` and explicit loader aliases in code and
    method references;
  - keep explanatory prose customer-readable by preferring "YAML",
    "workflow settings", and "JSON you want back" over internal jargon.

- [ ] Update harness GroundX API, GroundX Python, and architecture references
      that currently list `ingest` and `ingest_directories` as hand-written
      Python SDK helpers so they also list the promoted extraction workflow
      methods.

- [ ] Update harness evals and scanners so repeated invariants are machine
      checked where the repo already has a relevant gate:

  - SDK-helper discoverability should be represented in `groundx-python` or
    architecture evals when those files already test hand-written helper
    routing.
  - Extraction workflow template scanners should accept path-first
    create/update as preferred while keeping `workflow_sdk_kwargs(...)` as
    compatibility/offline support.
  - Generated plugin mirrors must be refreshed with `node scripts/sync-plugin.mjs`
    after source files change; do not edit `plugins/` directly. After any sync,
    rerun `node scripts/sync-plugin.mjs --check` and `node scripts/validate.mjs`.

- [ ] If any `harness-web-ui`, `harness-publish`, scaffold, or onboarding
      reference is changed during the scan, preserve these invariants:

  - authenticated product UI is the base product experience;
  - onboarding is a configurable overlay/app metadata flow;
  - onboarding does not become a separate anonymous base app or replacement for
    the authenticated shell.

- [ ] Run:

  ```bash
  python -m pytest skills/groundx-extraction-workflows/templates/test_compile_workflow.py skills/groundx-extraction-workflows/templates/test_imports.py -q
  node scripts/tests/test-groundx-extraction-workflows.mjs
  node scripts/tests/test-extraction-deploy-workflow.mjs
  node scripts/tests/test-evals.mjs
  node scripts/tests/test-harness-web-ui.mjs  # only if web-ui, scaffold, or onboarding references changed
  node scripts/sync-plugin.mjs --check
  node scripts/scans/scan-version-bump.mjs
  node scripts/validate.mjs
  git diff --check
  ```

  Expected: all pass. If plugin mirror sync reports expected generated diffs,
  run `node scripts/sync-plugin.mjs`, review the generated changes, rerun
  `node scripts/sync-plugin.mjs --check`, then rerun `node scripts/validate.mjs`
  before proceeding.

- [ ] Adversarial review:

  - Confirm fallback still works with older SDKs.
  - Confirm helper-backed deploy paths still write and validate offline compile
    artifacts before API calls.
  - Confirm scanners no longer require the old manual `workflow_sdk_kwargs`
    deployment path as the preferred path.
  - Confirm SDK-surface references document the promoted extraction workflow
    methods like `ingest` and `ingest_directories`.
  - Confirm source-of-truth surfaces, evals/scanners, generated plugin mirrors,
    and version/changelog surfaces are consistent with the harness contributor
    contract.
  - Confirm any touched web UI, scaffold, or onboarding references preserve the
    authenticated-base/onboarding-overlay model.
  - Confirm docs do not promise helper availability before SDK release.

## Phase 4: internal-arcadia-agents

**Repo:** `/Users/benjaminfletcher/git/internal-arcadia-agents`

**Files:**

- Modify conditionally: `prompts/arcadia_manager.py`
- Test: `prompts/test_arcadia_manager.py`
- Modify docs or OpenSpec notes only if helper adoption is not behaviorally
  equivalent.

- [ ] Add tests that use the existing `test_policy_metadata` fixture and compare
      first-class-method payloads to the current explicit workflow payloads.
      Equivalence means all of the following match:

  - `extract`, including `_groundx_persisted_extract`;
  - serialized `steps`;
  - `chunk_strategy`;
  - `section_strategy` for `update_prompts(...)`;
  - workflow `name`;
  - workflow `id` for update/repair paths.

  Add helper assertions in `prompts/test_arcadia_manager.py`:

  ```python
  def _plain(value):
      if hasattr(value, "model_dump"):
          return value.model_dump(by_alias=True)
      if hasattr(value, "dict"):
          return value.dict(by_alias=True)
      return value


  def _assert_arcadia_payload_equivalent(actual, expected):
      assert actual["extract"] == expected["extract"]
      assert _plain(actual["steps"]) == _plain(expected["steps"])
      assert actual.get("chunk_strategy") == expected.get("chunk_strategy")
      assert actual.get("section_strategy") == expected.get("section_strategy")
      assert actual.get("name") == expected.get("name")
      assert actual.get("id") == expected.get("id")
  ```

  Add a create equivalence test:

  ```python
  def test_create_extraction_workflow_helper_matches_arcadia_create_payload():
      man = TestManager(
          file_name="test_policy_metadata",
          workflow_id="test_policy_metadata",
      )
      expected = {
          "chunk_strategy": "element",
          "name": "test",
          "steps": man.workflow_steps(
              file_name="test_policy_metadata",
              workflow_id="test_policy_metadata",
          ),
          "extract": man.persisted_workflow_extract_dict(
              file_name="test_policy_metadata",
              workflow_id="test_policy_metadata",
          ),
      }
      prepared = prepare_arcadia_extraction_yaml(expected["extract"])
      definition = man.gx_client.load_extraction_definition_from_yaml(
          prepared=prepared,
      )
      calls = {}

      def create(**kwargs):
          calls["create"] = kwargs
          return types.SimpleNamespace(
              workflow=types.SimpleNamespace(workflow_id="created")
          )

      man.gx_client.workflows.create = create

      man.gx_client.create_extraction_workflow(
          definition=definition,
          name="test",
          steps=expected["steps"],
      )

      _assert_arcadia_payload_equivalent(calls["create"], expected)
      assert calls["create"]["extract"]["_groundx_persisted_extract"][
          "charges"
      ]["match_attrs"] == ["custom_match"]
  ```

  Add an update equivalence test:

  ```python
  def test_update_extraction_workflow_helper_matches_arcadia_update_payload():
      man = TestManager(
          file_name="test_policy_metadata",
          workflow_id="test_policy_metadata",
      )
      expected = {
          "id": "test_policy_metadata",
          "chunk_strategy": "element",
          "section_strategy": "page",
          "name": "test",
          "steps": man.workflow_steps(
              file_name="test_policy_metadata",
              workflow_id="test_policy_metadata",
          ),
          "extract": man.persisted_workflow_extract_dict(
              file_name="test_policy_metadata",
              workflow_id="test_policy_metadata",
          ),
      }
      prepared = prepare_arcadia_extraction_yaml(expected["extract"])
      definition = man.gx_client.load_extraction_definition_from_yaml(
          prepared=prepared,
      )
      calls = {}

      def update(id, **kwargs):
          calls["update"] = {"id": id, **kwargs}
          return types.SimpleNamespace(
              workflow=types.SimpleNamespace(workflow_id=id)
          )

      man.gx_client.workflows.update = update

      man.gx_client.update_extraction_workflow(
          "test_policy_metadata",
          definition=definition,
          name="test",
          section_strategy="page",
          steps=expected["steps"],
      )

      _assert_arcadia_payload_equivalent(calls["update"], expected)
      assert calls["update"]["extract"]["_groundx_persisted_extract"][
          "meters"
      ]["required_attrs"] == ["meter_number"]
  ```

- [ ] If the methods preserve Arcadia's metadata-key behavior, update
      `init_prompts`, `repair_prompts`, and `update_prompts` to call the
      first-class methods while still passing Arcadia's explicit
      `steps=self.workflow_steps(...)`.

- [ ] If the methods cannot preserve equivalent behavior, leave the existing
      explicit calls in place and add a short OpenSpec note explaining that
      Arcadia remains on the lower-level path because it owns specialized
      metadata-key handling.

- [ ] Run:

  ```bash
  pytest prompts/test_arcadia_manager.py -q
  pytest classes/test_extraction_reassembly.py -q
  git diff --check
  ```

  Expected: existing Arcadia prompt-manager and reassembly behavior remains
  unchanged except for the helper-backed create/update implementation if
  adopted.

- [ ] Adversarial review:

  - Confirm `qa_charges` and future `reconcile_fields`/`qa_fields`/`save_fields`
    planning remains untouched.
  - Confirm create/update payloads still include Arcadia workflow steps.
  - Confirm metadata-key behavior matches current tests.

## Phase 5: ADP And Related Repos Scan

**Repos:**

- `/Users/benjaminfletcher/git/adp-poc`

`groundx-agent-harness` is out of scope because it is generated from GroundX
Studio Harness. Phase 3 covers generated mirrors through source edits plus
plugin sync and sync checks.

- [ ] Inspect Phase 5 worktree status before scanning, and again before any
      edit:

  ```bash
  git -C /Users/benjaminfletcher/git/adp-poc status --short --branch
  ```

  Expected: scans can remain read-only, but do not edit any dirty Phase 5 repo
  without explicit direction.

- [ ] Before editing any Phase 5 repo, run the matching guard:

  ```bash
  # ADP repos: any dirty file blocks edits.
  test -z "$(git -C /Users/benjaminfletcher/git/adp-poc status --porcelain)" || {
    git -C /Users/benjaminfletcher/git/adp-poc status --short
    echo "/Users/benjaminfletcher/git/adp-poc is dirty; stop before editing"
    exit 1
  }
  ```

- [ ] Scan:

  ```bash
  PATTERN="prepare_extraction_yaml|workflow_sdk_kwargs|workflows\\.create|workflows\\.update|load_extraction_definition|create_extraction_workflow|update_extraction_workflow"

  rg -n "$PATTERN" \
    /Users/benjaminfletcher/git/adp-poc \
    --glob '!plugins/**' \
    --glob '!.agents/plugins/**' || true
  ```

- [ ] Update owned examples or scripts that still teach manual metadata copying.
      Before any edit, require that the target repo has no dirty non-generated
      source files, or stop and ask for direction.

- [x] Restore the whitespace-only ADP `prompt.yaml` local change before marking
      ADP scan complete.

- [ ] Run the narrow validation commands for any repo touched by this scan.

- [ ] Adversarial review:

  - Confirm no customer YAML content changed accidentally.
