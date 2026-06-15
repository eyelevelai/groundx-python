# Add Extraction Workflow Definition Methods Tasks

## Working State

- Central planning repo: `/Users/benjaminfletcher/git/groundx-python`
- Central planning branch: `codex/support-custom-workflow-steps-plan`
- SDK implementation worktree:
  `/Users/benjaminfletcher/git/groundx-python-support-custom-workflow-steps-sdk`
  on `codex/support-custom-workflow-steps-sdk`
- Harness implementation worktree:
  `/Users/benjaminfletcher/git/groundx-studio-harness-support-custom-workflow-steps`
  on `codex/support-custom-workflow-steps-harness`
- Public docs repo:
  `/Users/benjaminfletcher/git/eyelevel-fern-config` on
  `codex/support-custom-workflow-steps-fern`
- Arcadia repo:
  `/Users/benjaminfletcher/git/internal-arcadia-agents` on
  `codex/extraction-reassembly-metadata`
- ADP repo:
  `/Users/benjaminfletcher/git/adp-poc` on
  `codex/support-custom-workflow-steps-adp`

## Tasks

- [x] Validate this OpenSpec change in the central planning repo.
- [x] Refresh every implementation branch against its current target branch
      before coding. At minimum refresh the SDK branch against current
      `origin/main`, the Fern docs branch against current `origin/main`, and the
      harness branch against current `origin/main`; refresh Arcadia against its
      configured upstream before any Arcadia edits. Then rerun the narrow
      baseline checks for any branch that already contains custom-step work.
      Stop before rebasing if a worktree is dirty; do not stash, commit, or
      overwrite dirty files without explicit direction.
- [x] In `groundx-python`, add failing tests for the public high-level API:
      `ExtractionDefinition`,
      `client.load_extraction_definition(...)`,
      `client.load_extraction_definition_from_yaml(...)`,
      `client.load_extraction_definition_from_workflow(...)`,
      `client.create_extraction_workflow(...)`, and
      `client.update_extraction_workflow(...)`.
- [x] Add concrete async parity tests for the same client methods on
      `AsyncGroundX`, including awaited YAML loading, workflow-ID loading,
      create, update, and one-source validation failures.
- [x] Add tests proving create/update use `definition` before YAML/prepared
      sources, and reject ambiguous YAML/prepared sources when `definition` is
      absent. Include cases where `mapping_kind` is provided without `mapping`
      as the selected source.
- [x] Add tests proving `mapping` source handling is explicit for all supported
      shapes: authored YAML-shaped mapping by default, persisted workflow
      `extract` mapping with authored metadata only when
      `mapping_kind="workflow_extract"`, and execution-only workflow `extract`
      mapping that loads with `prepared=None` only when
      `mapping_kind="workflow_extract"`.
- [x] Add tests proving workflow template values must be strings and that
      placeholder-style template keys such as `{{LANGUAGE}}` and
      `{{LANGUAGE_UNKNOWN}}` are preserved exactly, including an empty-string
      value for `{{LANGUAGE_UNKNOWN}}`.
- [x] Add tests proving workflow-ID loading fetches an existing workflow,
      extracts the persisted extraction config, and fails clearly for workflows
      without extraction config.
- [x] Add tests using real generated `WorkflowResponse` / `WorkflowDetail`
      models proving workflow-ID loading preserves top-level `template`,
      `custom_steps`, `output_routes`, `leaf_fields`, `chunk_strategy`,
      `section_strategy`, and `steps`, with persisted `extract["workflow"]`
      used only as fallback.
- [x] Add tests proving workflow-loaded definitions with no
      `_groundx_persisted_extract` return `prepared=None` while still preserving
      create/update payload fields.
- [x] Add import-boundary tests proving `import groundx` and
      `from groundx import GroundX, AsyncGroundX` do not import optional extract
      dependencies at module import time, and extraction methods raise a clear
      `pip install groundx[extract]` hint when those dependencies are missing.
- [x] Before adding any new hand-written test under `tests/custom`, update or
      verify `.fernignore` protects `tests/custom` so the test survives SDK
      regeneration.
- [x] Add tests proving custom metadata copying, generated workflow-client wire
      serialization, and custom-step fixed-default disabling. The fixed-default
      disabling tests must assert the exact disabled `WorkflowSteps` overlay:
      `chunk_instruct`, `chunk_keys`, `chunk_summary`, `doc_keys`,
      `doc_summary`, `sect_instruct`, and `sect_summary` are present and set to
      `None` before serialization, and the generated JSON body carries the
      corresponding disabled fixed-step keys.
- [x] Add sync and async tests proving `request_options` passed to
      `create_extraction_workflow(...)` and `update_extraction_workflow(...)`
      reaches the generated workflow create/update calls.
- [x] Implement `ExtractionDefinition` in a focused hand-written extract module
      and export it from `groundx.extract`.
- [x] Implement private/internal workflow kwargs assembly from
      `ExtractionDefinition`. Do not promote this as a public method or docs
      technique.
- [x] Implement `GroundX.load_extraction_definition_from_yaml(...)` and
      `GroundX.load_extraction_definition_from_workflow(...)` in the
      hand-written SDK client subclass, not in generated Fern files.
- [x] Implement `GroundX.load_extraction_definition(...)` as the promoted
      consolidated loader. It must use `workflow_id` before YAML/prepared
      sources; when `workflow_id` is absent, it must accept exactly one of
      `path`, `yaml_text`, `mapping`, or `prepared`.
- [x] Use lazy imports from `src/groundx/ingest.py` into the extract workflow
      module so the base SDK remains usable without the `extract` extra.
- [x] Implement `GroundX.create_extraction_workflow(...)` and
      `GroundX.update_extraction_workflow(...)` so they accept an
      `ExtractionDefinition` or YAML shortcut source and delegate to generated
      workflow create/update calls.
- [x] Implement async parity on `AsyncGroundX`.
- [x] Document the promoted loader/create/update methods in the SDK with method
      docstrings and README or reference coverage comparable to `ingest` and
      `ingest_directories`. Public examples should show path-first
      create/update; definition loading is for inspection, reuse, or copying
      settings.
- [x] Document that extraction definition methods require `groundx[extract]`,
      while importing and using the base SDK does not.
- [x] Verify `prepare_extraction_yaml(...)`, `PreparedExtractionYaml`,
      `load_from_yaml(...)`, and `load_from_mapping(...)` remain available and
      unchanged for lower-level callers, but are not promoted as the normal
      workflow-management path.
- [x] Run SDK narrow tests for the new methods, generated workflow-client wire
      serialization, and existing extract YAML custom workflow tests.
- [x] Run SDK type checks and broader custom/extract tests.
- [x] Run SDK CI-equivalent async coverage, including the aiohttp-marked test
      gate after installing the aiohttp extra.
- [x] After SDK implementation passes local gates, merge and publish the Python
      SDK only after the custom-step deployed-path blocker is resolved. Then
      verify the published package in a fresh environment before allowing public
      docs or harness helper-preference PRs to merge.
      Closeout: merged through `groundx-python` PRs #16/#17 and published as
      `groundx==3.6.7`; package availability was verified through PyPI JSON.
- [x] In `eyelevel-fern-config`, update
      `fern/pages/extract-data-from-documents.mdx` so the primary workflow
      create and update examples pass a YAML path directly to the new
      create/update helpers.
- [x] Add method-level public docs for
      `client.load_extraction_definition(...)`,
      `client.load_extraction_definition_from_yaml(...)`,
      `client.load_extraction_definition_from_workflow(...)`,
      `client.create_extraction_workflow(...)`, and
      `client.update_extraction_workflow(...)`, including explicit workflow
      assignment after create and the exact-one-source rule for the loader.
- [x] Keep Fern/OpenAPI schema names unchanged unless a separate schema-naming
      plan is created and approved.
- [x] Validate Fern docs with the repo's docs checks.
- [x] Keep the Fern docs PR draft-only until the published Python SDK helper
      methods are verified from the released package.
      Closeout: Fern docs merged after SDK publication.
- [x] In `groundx-studio-harness`, update deploy/run/batch/prompt-manager
      templates to prefer the first-class loader/create/update methods when
      installed.
- [x] Keep `workflow_sdk_kwargs(...)` for offline compile artifacts and fallback
      until the minimum supported SDK version includes the helper methods.
- [x] Update harness scanners, references, evals, and source surfaces so they
      teach path-first create/update as the preferred SDK path and definition
      loading as the reuse/inspection path; refresh generated plugin mirrors
      only through the repo-approved sync command.
- [x] Update harness API-surface and Python SDK references that list
      hand-written methods so the promoted extraction workflow methods appear
      beside `ingest` and `ingest_directories`.
- [x] Update `skills/groundx-extraction-workflows/references/public-docs.md`
      so its public-doc flow prefers the new helper methods and no longer
      teaches `prepare_extraction_yaml(...)` as the primary public path.
- [x] Check/update harness source-of-truth surfaces when touched:
      `skills/routing.manifest.json`, owning `SKILL.md` files,
      `references/README.md`, skill `evals/evals.json`, scanner fixtures or
      expectations, generated plugin mirror sync output, changelog/version
      surfaces, and README generator output. Do not edit or scan `plugins/`
      mirror files directly unless the task is plugin packaging.
- [x] If any `harness-web-ui`, `harness-publish`, scaffold, or onboarding
      reference is touched, preserve the product invariant that the base
      experience is an authenticated app shell and onboarding is a configurable
      overlay/app metadata flow.
- [x] Run harness Python template tests, Node scanner/eval tests, plugin sync
      checks, and full validation.
- [x] Keep harness helper-preference changes draft-only until the published
      Python SDK helper methods are verified and the minimum supported SDK
      version is updated or fallback behavior is proven.
      Closeout: harness retained fallback behavior while preferring the helper
      methods when installed.
- [x] In `internal-arcadia-agents`, add tests using the existing
      `test_policy_metadata` fixture that compare first-class-method behavior
      to the existing explicit workflow calls. The comparison must cover
      `extract`, `_groundx_persisted_extract`, serialized `steps`,
      `chunk_strategy`, `section_strategy`, workflow `name`, and update `id`.
- [x] Adopt the methods in Arcadia only if tests prove equivalent behavior;
      otherwise record a no-op decision and leave existing explicit workflow
      calls in place.
- [x] Scan `adp-poc` for manual workflow create/update
      boilerplate. Exclude generated plugin mirror directories from the scan,
      inspect worktree status first, and update only clean, owned examples or
      scripts. `groundx-agent-harness` is out of scope because it is generated
      from GroundX Studio Harness.
- [x] Run OpenSpec validation in every repo whose OpenSpec changes are touched.
- [x] Run an adversarial review after each repo checkpoint before starting the
      next repo.
- [x] Keep SDK/docs publishing and downstream dependency bumps blocked until the
      existing custom-step deployed-path e2e blocker is resolved.
      Closeout: SDK/docs publication was allowed for the helper-method release;
      the separate central custom-step release/E2E plan remains active for the
      runtime deployed-path proof.

## Execution Evidence And Open Blockers

Updated 2026-06-14.

Completed local implementation and verification:

- SDK worktree `/Users/benjaminfletcher/git/groundx-python-support-custom-workflow-steps-sdk`:
  implemented `ExtractionDefinition`, sync/async load/create/update helpers,
  lazy extract imports, request-options propagation, explicit mapping-kind
  handling, workflow-ID load, fixed-step disabling, and README/docstring
  coverage. Verification run:
  `poetry run pytest -q`,
  `poetry run pyright`,
  `poetry run ruff check ...touched files...`,
  `poetry install --extras aiohttp`,
  `poetry run pytest -q -rs -m aiohttp .`,
  `git diff --check`.
- Fern docs repo `/Users/benjaminfletcher/git/eyelevel-fern-config`:
  updated `fern/pages/extract-data-from-documents.mdx` to teach
  path-first `create_extraction_workflow` and `update_extraction_workflow`,
  plus `load_extraction_definition`, explicit YAML/workflow loader aliases, and
  method-level public docs covering parameters, returns, examples, extract
  extra requirements, exact-one-source validation, explicit workflow assignment
  after create, and full-update semantics. Verification run: `fern check`,
  `git diff --check`.
- Harness repo
  `/Users/benjaminfletcher/git/groundx-studio-harness-support-custom-workflow-steps`:
  updated deploy/run/batch/prompt-manager templates to prefer helper methods
  with `workflow_sdk_kwargs(...)` fallback, updated public docs/reference/API
  surfaces, updated scanner expectations, and synced generated plugin mirrors
  through `node scripts/sync-plugin.mjs`. Verification run:
  `node scripts/tests/test-extraction-deploy-workflow.mjs`,
  `node scripts/tests/test-groundx-extraction-workflows.mjs`,
  `python -m pytest skills/groundx-extraction-workflows/templates/test_compile_workflow.py skills/groundx-extraction-workflows/templates/test_imports.py -q`,
  `node scripts/sync-plugin.mjs --check`,
  `node scripts/validate.mjs`,
  `git diff --check`.
- Arcadia repo `/Users/benjaminfletcher/git/internal-arcadia-agents`:
  added helper-backed create/update path with old-SDK fallback, kept explicit
  Arcadia `steps`, and added payload equivalence tests for persisted extract,
  `_groundx_persisted_extract`, steps, chunk/section strategy, name, and update
  ID. Verification run:
  `PYTHONPATH=$PWD pytest prompts/test_arcadia_manager.py -q`,
  `PYTHONPATH=$PWD pytest classes/test_extraction_reassembly.py -q`,
  `git diff --check`.

Post-review fixes applied 2026-06-14:

- Plan, SDK, docs, and harness guidance now promote
  `client.create_extraction_workflow(path=...)` and
  `client.update_extraction_workflow(id, path=...)` for the common YAML flow.
  `client.load_extraction_definition(...)` is promoted for inspection, reuse,
  and copying existing workflow settings, with explicit YAML/workflow aliases
  retained for source-specific callers.
- Arcadia now prefers `load_extraction_definition(prepared=...)` when the SDK
  exposes it and falls back to `load_extraction_definition_from_yaml(prepared=...)`
  for older SDKs.
- Harness `run_extraction.py --reuse-workflow` now loads the existing extraction
  definition when the SDK helper is available, so X-Ray fallback keeps the
  workflow extract metadata and output routes.
- Harness `prompt_manager.py` old-SDK fallback now uses the generated workflow
  client's `id` argument for `workflows.update(...)` and `workflows.get(...)`.
- Arcadia repair prompt tests now cover the helper-backed workflow update path.
- Harness deploy template tests now cover helper-backed create/update and keep
  old-SDK fallback coverage on the corrected `yaml_path` function contract.
- SDK helper docstrings now include method-level parameter, return, example,
  and update-semantics coverage, with a regression test enforcing those
  sections for the promoted helper methods.
- Fern public docs now include method-level helper reference sections for the
  promoted extraction workflow helpers instead of only guide snippets.
- `execution-plan.md` now states that its detailed checkboxes are the original
  execution recipe and that this file is the authoritative current tracker.

Open blockers / not yet executable:

- SDK publish and downstream merge gates remain blocked until the custom-step
  deployed-path e2e blocker is resolved and the released SDK package is verified
  from a fresh environment.
- `groundx-agent-harness` is out of scope because it is generated from GroundX
  Studio Harness; do not edit it directly for this plan.
- ADP scan complete: `/Users/benjaminfletcher/git/adp-poc` had only
  whitespace-only local changes in `workflows/adp_401k_v1/prompt.yaml`; those
  no-op changes were removed and the worktree is clean. The ADP scan found no
  manual extraction workflow helper boilerplate to update.
- The detached `adp-poc-support-custom-workflow-steps` worktree had no local
  work and was removed after scan-only verification.
