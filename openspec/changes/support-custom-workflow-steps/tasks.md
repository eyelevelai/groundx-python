# Support Custom Workflow Steps Execution Plan

> **For agentic workers:** REQUIRED SUB-SKILLS: Use
> `superpowers:brainstorming` for design refinement,
> `superpowers:test-driven-development` for each implementation task, and
> `superpowers:verification-before-completion` before claiming completion.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a durable, tested workflow model for custom chunk, section, and
document extraction steps, while preserving legacy fixed-slot YAML and workflow
behavior.

**Architecture:** Start with a source-backed trace of `chunk-keywords` plus
representative section and document output paths, then add a typed custom-step
workflow config through Fern/OpenAPI, Go runtime, Python SDK, Arcadia runtime,
harness skills, public docs, and ADP YAML. Keep fixed steps as the
legacy/default path and use allowlisted runtime orchestration in Arcadia.

**Tech Stack:** OpenAPI/Fern, Python SDK/Pydantic/PyYAML/pytest, Go workflow
models/processors/X-Ray tests, Celery/pytest in Arcadia, Node harness scanners.

---

## Ground Rules

- Do not change existing tests only to make them pass.
- Existing tests may be changed only with explicit user/reviewer feedback or
  overwhelming evidence that the test no longer represents correct behavior.
- Prefer adding new regression tests beside existing tests.
- Preserve legacy YAML and legacy workflow behavior.
- Preserve authored YAML/custom metadata in `workflow.extract`.
- Publish public docs only after runtime, SDK, and harness behavior has been
  verified, as the final prerequisite before e2e if the e2e path requires
  published docs.
- Downstream repos must depend on `groundx-python >= <released version>`, not an
  exact SDK version pin.
- After Task 2 locks the contract, do not begin code changes until repo-specific
  implementation plans exist with exact failing tests, expected failures,
  implementation steps, verification commands, and commit checkpoints.
- For `internal-arcadia-agents`, the current gate requires only a deferral stub
  that records preserved legacy behavior and the follow-on plan boundary; the
  full `reconcile_fields` / `qa_fields` / `save_fields` implementation plan is
  created after central cleanup and closeout.
- Tasks 4-12 are blocked until Tasks 1-3 are complete, reviewed, and updated in
  this OpenSpec change. Treat the later tasks as scope inventory until then.
- Before any implementation task starts, create or select a clean isolated
  branch or worktree in that repo and record any unrelated local changes that
  must not be mixed into this work.
- Do not publish generated SDKs or public docs early. Publishing is allowed only
  after local/runtime/schema/SDK/harness verification, as the final prerequisite
  before the e2e path that requires published artifacts.
- Local generated SDK artifacts may be used for tests before release; downstream
  dependency bumps are blocked until the published-artifact e2e path passes.
- Generated SDK files in `groundx-python` must come from the upstream
  Fern/OpenAPI source and approved regeneration or release path. Do not hand-edit
  or commit generated files as implementation work outside that path.
- The fresh-scan correction in
  `fresh-scan-generated-sdk-and-xray-corrections.md` is mandatory closeout
  scope. Documentation and implementation must be checked across the OpenSpec
  plan PR, SDK helpers PR, Fern docs PR, Studio Harness PR, Arcadia PR, ADP PR,
  and the Cashbot runtime/API work.
- Run an adversarial review after each task before starting the next task.
- Keep repo changes narrow and repo-owned.

## Task 1: Complete The Cross-Repo Trace

**Files to read:**

- `/Users/benjaminfletcher/git/adp-poc/workflows/adp_401k_v1/prompt.yaml`
- `/Users/benjaminfletcher/git/adp-poc/workflows/adp_401k_v1/conversion_report.json`
- `/Users/benjaminfletcher/git/eyelevel-fern-config/fern/openapi.yml`
- `/Users/benjaminfletcher/git/groundx-python/src/groundx/types/workflow_steps.py`
- `/Users/benjaminfletcher/git/groundx-python/src/groundx/types/workflow_step_config.py`
- `/Users/benjaminfletcher/git/groundx-python/src/groundx/types/workflow_step_config_field.py`
- `/Users/benjaminfletcher/git/groundx-python/src/groundx/extract/classes/groundx.py`
- `/Users/benjaminfletcher/git/groundx-python/src/groundx/extract/classes/document.py`
- `/Users/benjaminfletcher/git/groundx-python/src/groundx/extract/prompt/utility.py`
- `/Users/benjaminfletcher/git/cashbot-go/pkg/model/summarizer/process.go`
- `/Users/benjaminfletcher/git/cashbot-go/pkg/model/summarizer/step_type.go`
- `/Users/benjaminfletcher/git/cashbot-go/pkg/model/summarizer/field_type.go`
- `/Users/benjaminfletcher/git/cashbot-go/pkg/model/completions/eyelevel/process.go`
- `/Users/benjaminfletcher/git/cashbot-go/pkg/model/prompt/templates.go`
- `/Users/benjaminfletcher/git/cashbot-go/pkg/processor/summarizer/chunks.go`
- `/Users/benjaminfletcher/git/cashbot-go/pkg/processor/summarizer/sections.go`
- `/Users/benjaminfletcher/git/cashbot-go/pkg/processor/summarizer/document.go`
- `/Users/benjaminfletcher/git/cashbot-go/pkg/processor/summarizer/request.go`
- `/Users/benjaminfletcher/git/cashbot-go/pkg/processor/summarizer/execute.go`
- `/Users/benjaminfletcher/git/cashbot-go/pkg/processor/summarizer/util.go`
- `/Users/benjaminfletcher/git/cashbot-go/pkg/processor/summarizer/processor.go`
- `/Users/benjaminfletcher/git/cashbot-go/pkg/model/layout/chunk.go`
- `/Users/benjaminfletcher/git/cashbot-go/pkg/model/layout/document.go`
- `/Users/benjaminfletcher/git/cashbot-go/pkg/model/layout/search_meta.go`
- `/Users/benjaminfletcher/git/cashbot-go/pkg/model/layout/custom_meta.go`
- `/Users/benjaminfletcher/git/cashbot-go/pkg/model/layout/xray.go`
- `/Users/benjaminfletcher/git/cashbot-go/pkg/partner/request.go`
- `/Users/benjaminfletcher/git/cashbot-go/pkg/partner/workflow.go`
- `/Users/benjaminfletcher/git/internal-arcadia-agents/prompts/arcadia_manager.py`
- `/Users/benjaminfletcher/git/internal-arcadia-agents/classes/arcadia_agent_request.py`
- `/Users/benjaminfletcher/git/internal-arcadia-agents/classes/statement.py`
- `/Users/benjaminfletcher/git/internal-arcadia-agents/classes/extraction_reassembly.py`
- `/Users/benjaminfletcher/git/internal-arcadia-agents/tasks/download.py`
- `/Users/benjaminfletcher/git/internal-arcadia-agents/tasks/agent.py`
- `/Users/benjaminfletcher/git/internal-arcadia-agents/tasks/save.py`
- `/Users/benjaminfletcher/git/groundx-studio-harness/skills/groundx-extraction-workflows/templates/compile_workflow.py`
- `/Users/benjaminfletcher/git/groundx-studio-harness/skills/groundx-extraction-workflows/templates/xray_to_extract.py`
- `/Users/benjaminfletcher/git/groundx-studio-harness/skills/groundx-extraction-workflows/templates/validate_workflow_json.py`
- `/Users/benjaminfletcher/git/groundx-studio-harness/skills/groundx-extraction-workflows/SKILL.md`
- `/Users/benjaminfletcher/git/groundx-studio-harness/skills/groundx-extraction-workflows/SKILL.public.md`
- `/Users/benjaminfletcher/git/groundx-studio-harness/skills/groundx-extraction-workflows/evals/evals.json`
- `/Users/benjaminfletcher/git/groundx-studio-harness/scripts/tests/test-groundx-extraction-workflows.mjs`

- [x] Trace `chunk-keys` from workflow config to Go `StepType`.
- [x] Trace `chunk-keys` from Go `FieldType` to chunk storage.
- [x] Trace `chunkKeywords` from Go X-Ray output to Python SDK parsing.
- [x] Trace `sect-summary`/`sect-sum` from workflow config to Go processing,
      storage, X-Ray output, SDK parsing, harness aggregation, and Arcadia use.
- [x] Trace `doc-summary`/`doc-sum` from workflow config to Go processing,
      storage, X-Ray output, SDK parsing, harness aggregation or lack of
      aggregation, and Arcadia use.
- [x] Trace `chunkKeywords` through harness local X-Ray aggregation.
- [x] Trace `chunkKeywords` through Arcadia routed reassembly tests.
- [x] Trace `Process.Template` from workflow JSON load to prompt rendering.
- [x] Trace current reserved top-level YAML key handling.
- [x] Decide how a new `workflow:` authoring section avoids stealing a legacy
      final group: top-level `workflow:` is always reserved, and attempted final
      groups named `workflow` fail clearly.
- [x] Identify every place a custom step name must survive serialization.
- [x] Identify every place a custom output value must be stored and read:
      custom outputs are stored in explicit workflow custom-output metadata,
      surfaced through `customChunkOutputs`, `customSectionOutputs`, and
      `customDocumentOutputs`, and routed to final JSON through route metadata.
- [x] Identify every harness scanner, eval, example, and reference that teaches
      or enforces the old fixed-slot model.
- [x] Update `chunk-keywords-trace.md` with missing code points.
- [x] Adversarial review: confirm the trace follows real runtime paths for
      chunk, section, and document outputs, not only tests or docs.
- [x] Fresh-scan correction recorded for generated SDK boundary and X-Ray
      runtime/readback coverage across all touched repos.

## Task 2: Finalize The Public Contract

**Files to update:**

- This change folder's `design.md`
- This change folder's `specs/extract-yaml/spec.md`
- This change folder's `specs/workflow-config/spec.md`
- This change folder's `specs/custom-output-readback/spec.md`
- This change folder's `specs/arcadia-runtime/spec.md`
- This change folder's `specs/release-governance/spec.md`
- This change folder's `specs/cross-repo-planning/spec.md`

- [x] Decide the OpenAPI shape for custom steps: add workflow-level
      `customSteps` while preserving existing `steps`.
- [x] Decide the exact public `customSteps[]` item shape: `name`, `level`,
      `kind`, optional `config`, and optional `requiredTemplateKeys`; custom
      step `config` uses the existing element-targeted workflow step shape but
      omits or nulls the legacy fixed-output `field`.
- [x] Decide the custom output X-Ray shape: use `customChunkOutputs`,
      `customSectionOutputs`, and `customDocumentOutputs`, while preserving
      fixed legacy fields.
- [x] Decide the exact route metadata shape from each custom output path back
      to its final JSON path: each route records `workflow_group`,
      `workflow_field`, `final_path`, `step_name`, `level`, `output_map`,
      `output_key`, and `readback_path`.
- [x] Decide the public route-record container: direct public workflow config uses
      workflow-level `outputRoutes`, and persisted metadata uses
      `workflow.extract.workflow.output_routes`.
- [x] Decide the public leaf-field container: direct public workflow config uses
      workflow-level `leafFields`, and persisted metadata uses
      `workflow.extract.workflow.leaf_fields`.
- [x] Decide route/leaf integrity: every `outputRoutes` record must have exactly
      one matching `leafFields` record, and every `leafFields` record must have
      exactly one matching `outputRoutes` record, using final path, workflow
      group/field, custom step, level, and output key.
- [x] Decide where explicit output keys are authored: YAML uses field-level
      `workflow_output_key`, persisted route metadata uses `output_key`, and
      public JSON route records use `outputKey`.
- [x] Decide how YAML workflow group metadata points to a custom step name:
      `workflow_step: <step-name>` is the forward path; legacy `slot:` remains
      supported for existing fixed-slot YAML.
- [x] Decide whether `workflow:` is the reserved YAML authoring section and how
      legacy final groups named `workflow` behave: top-level `workflow:` is
      always reserved; no known legacy final group exists, and attempted final
      groups named `workflow` fail clearly.
- [x] Replace the default opt-in rule: there is no opt-in rule; top-level
      `workflow:` is always authoring metadata.
- [x] Decide how `template` is represented in public workflow config: expose
      workflow/process config matching cashbot-go `Process.Template
      *map[string]string`; do not expose the separate partner template object;
      YAML-authored template values live at workflow-level `workflow.template`.
- [x] Decide `template` validation boundaries for unknown keys, missing required
      keys, reserved keys, invalid value types, payload size, escaping/rendering
      failures, and fixed/custom prompt behavior; required keys are declared by
      step metadata, not inferred from prompt parsing, and validate with the same
      normalization/rules as template keys.
- [x] Decide the maximum field count for one executable workflow step and the
      layer that hard-fails validation: 20 fields, hard-failed by public
      API/runtime validation and mirrored by SDK, harness, and ADP validation.
- [x] Record the exact initial Arcadia task vocabulary: keep existing
      reconcile/QA/save tasks except `qa_charges`, treat `agent`/`save_agents`
      as internal compatibility nodes, classify `qa_charges` as dead legacy, and
      defer `reconcile_fields`/`qa_fields`/`save_fields` to a follow-on plan.
- [x] Decide TypeScript feature-support scope and the mandatory TypeScript
      generation smoke coverage. TypeScript generation compatibility is required
      because the shared Fern schema feeds the TypeScript SDK; use
      `fern generate --group ts-sdk`.
- [x] Decide downstream release/version gates, including the minimum
      `groundx-python >= <released version>` required by Arcadia and harness
      after the published-artifact e2e path passes.
- [x] Decide the publish-last gate: generated SDK/docs publishing is allowed only
      after local/runtime/schema/SDK/harness verification and immediately before
      the e2e path that requires published artifacts; downstream dependency
      bumps wait until that e2e path passes.
- [x] Decide the draft-generation path: Fern/OpenAPI branch, local
      Python/TypeScript generation or smoke output, runtime and SDK verification
      against the draft contract, then public SDK/docs publishing as the final
      e2e prerequisite.
- [x] Decide custom step naming rules: valid characters, canonical form,
      case/kebab/snake/camel conversion, uniqueness scope, reserved names,
      collision behavior with fixed step names, and duplicate output destination
      behavior.
- [x] Decide the persisted `workflow.extract` metadata version and behavior for
      missing, unknown, old, and future versions: `workflow.metadata_version: 1`
      is current; unknown/future versions fail closed; missing metadata is
      legacy fallback only when no custom workflow metadata is present.
- [x] Decide how field-load validation is enforced by the public API/runtime, SDK
      YAML preparation, harness validation, and ADP validation. Direct API users
      must be protected by the public API/runtime path; the limit is 20 fields
      per executable workflow step.
- [x] Decide the field-count source for public API/runtime validation:
      server-recomputed counts from canonical
      `workflow.extract.workflow.output_routes` and
      `workflow.extract.workflow.leaf_fields`; caller-provided
      `field_counts` and `schema_hash` are non-authoritative hints that must
      match when present.
- [x] Decide the exact field-count hash input: `metadata_version`,
      `custom_steps`, `output_routes`, and `leaf_fields` with prompt prose,
      examples, model parameters, and template values excluded.
- [x] Decide exact `leaf_fields` repetition metadata: persisted
      `is_repeated`/`repetition_scope`, public `isRepeated`/`repetitionScope`,
      and allowed `repetition_scope` values `none`, `field`, and `item`.
- [x] Decide repeated-item path semantics: `repetition_scope: item` uses a
      literal `*` RFC 6901 path segment as the schema wildcard, such as
      `/fees/*/amount`, and counts once per prompted schema leaf.
- [x] Decide exact reserved template metadata names and require the same list for
      `template` and `requiredTemplateKeys`.
- [x] Decide deterministic hash sorting: `custom_steps` by `(name)`,
      `output_routes` by `(final_path, workflow_group, workflow_field,
      step_name, output_key)`, and `leaf_fields` by `(final_path,
      workflow_group, workflow_field, step_name, output_key)`.
- [x] Decide custom output persistence, storage migration/backward compatibility,
      and readback behavior for existing documents and workflows.
- [x] Decide exact legacy fallback semantics.
- [x] Add examples for one custom chunk step, one custom section step, and one
      custom document step.
- [x] Adversarial review: confirm the contract separates step identity, output
      field, extraction group, and final JSON group.

## Task 3: Create Repo-Specific Implementation Plans

**Repos:**

- `/Users/benjaminfletcher/git/eyelevel-fern-config`
- `/Users/benjaminfletcher/git/cashbot-go`
- `/Users/benjaminfletcher/git/groundx-python`
- `/Users/benjaminfletcher/git/internal-arcadia-agents`
- `/Users/benjaminfletcher/git/groundx-studio-harness`
- `/Users/benjaminfletcher/git/adp-poc`

**Repo-owned planning artifacts to create or update:**

- Valid OpenSpec change folders in each repo that owns durable behavior:
  - `/Users/benjaminfletcher/git/eyelevel-fern-config/openspec/changes/support-custom-workflow-steps/`
  - `/Users/benjaminfletcher/git/cashbot-go/openspec/changes/support-custom-workflow-steps/`
  - `/Users/benjaminfletcher/git/groundx-python/openspec/changes/support-custom-workflow-steps-sdk/`
  - `/Users/benjaminfletcher/git/groundx-studio-harness/openspec/changes/support-custom-workflow-steps/`
  - `/Users/benjaminfletcher/git/adp-poc/openspec/changes/support-custom-workflow-steps/`
- A non-implementation deferral stub for
  `/Users/benjaminfletcher/git/internal-arcadia-agents` that states no current
  code changes begin there and the full custom field-action plan is created
  after central cleanup/closeout.
- Each repo OpenSpec change folder must include `proposal.md`, `tasks.md`, and
  `execution-plan.md`.
- Each repo OpenSpec change folder must include `specs/<capability>/spec.md`
  deltas for durable behavior owned by that repo.
- If a repo only needs tactical notes and no durable spec delta, store those
  notes outside `openspec/changes/`; do not create an execution-plan-only
  OpenSpec change folder.

- [x] Create or update one repo-owned execution plan in every repo that will
      receive current-wave changes.
- [x] Confirm every repo-owned OpenSpec change is independently valid and
      archiveable, or move non-OpenSpec notes out of `openspec/changes/`.
- [x] Each repo plan must name exact files, exact failing tests, expected
      failures, implementation steps, verification commands, and commit
      checkpoints.
- [x] Each repo plan must state generated-file boundaries and release
      dependencies.
- [x] Each repo plan that consumes generated SDK/API surfaces must state whether
      generated artifacts are local verification output or release-produced files
      that may be committed.
- [x] Each repo plan must state the branch/worktree to use and confirm whether
      the repo was clean before implementation began.
- [x] Each repo plan must state the repo-specific publish-last release gate and how
      it depends on upstream runtime/API, SDK, harness, or documentation changes.
- [x] The `internal-arcadia-agents` deferral stub must state the preserved legacy
      behavior, the exclusion of `qa_charges` from future authorable vocabulary,
      and the follow-on boundary for `reconcile_fields`, `qa_fields`, and
      `save_fields`.
- [x] The main plan must link to each repo-owned execution plan in dependency
      order and to the `internal-arcadia-agents` deferral stub.
- [x] Adversarial review: confirm no implementation task below begins until the
      repo-specific plans and the Arcadia deferral stub are complete and reviewed.

## Task 4: Update Fern/OpenAPI Contract

**Repo:** `/Users/benjaminfletcher/git/eyelevel-fern-config`

**Likely files:**

- `fern/openapi.yml`
- `fern/generators.yml`
- generated smoke output or review notes for `python-sdk` and `ts-sdk`

- [x] Add failing OpenAPI/schema checks or exact diffs for `customSteps`,
      custom step `config`, custom step legacy `field` rejection, `outputRoutes`,
      `outputKey`, `leafFields`, route/leaf one-to-one validation, `isRepeated`,
      `repetitionScope`, wildcard repeated-item final paths, `template`,
      `requiredTemplateKeys`, reserved template key names, custom output maps, and
      field-count metadata.
- [x] Add `template` to the workflow config schema.
- [x] Add the custom-step and custom route schemas chosen in Task 2.
- [x] Keep existing fixed `WorkflowSteps` fields.
- [x] Run `fern generate --group ts-sdk` as the TypeScript generation smoke
      check. If generation cannot pass, block the schema change instead of
      treating generator compatibility as out of scope.
- [x] Run `fern check` and `fern generate --docs` as local docs/OpenAPI
      validation. Do not publish docs until the publish-last gate opens.
      Note: `fern check` passed. Release-mode TypeScript generation requires
      `NPM_TOKEN`, so the successful smoke command was
      `fern generate --group ts-sdk --local --no-require-env-vars --no-prompt`.
      `fern generate --docs --preview --skip-upload --no-require-env-vars
      --no-prompt` reached 0 docs-definition errors, then attempted remote
      preview publishing and failed with `User does not belong to organization`;
      docs publish remains gated on Fern org access during publish-last.
- [x] Adversarial review: confirm the schema is additive, generated SDKs can
      represent it, and no public docs describe unverified behavior yet.

## Task 5: Update cashbot-go Models, Loading, Processing, And X-Ray

**Repo:** `/Users/benjaminfletcher/git/cashbot-go`

Status: completed in worktree
`/Users/benjaminfletcher/git/cashbot-go-support-custom-workflow-steps` on
branch `codex/support-custom-workflow-steps-runtime` and committed as
`4e8b0ef6a`. The Fern mirror endpoint correction is committed in
`eyelevel-fern-config` as `cf393f5`. Plan-specific targeted Go packages pass;
`go test ./...` remains blocked by repo-wide generated `version.go`
prerequisites and external service/state dependencies.

**Likely files:**

- `pkg/model/summarizer/process.go`
- `pkg/model/summarizer/step.go`
- `pkg/model/summarizer/step_type.go`
- `pkg/model/summarizer/field_type.go`
- `pkg/model/completions/eyelevel/process.go`
- `pkg/model/prompt/templates.go`
- `pkg/processor/summarizer/chunks.go`
- `pkg/processor/summarizer/sections.go`
- `pkg/processor/summarizer/document.go`
- `pkg/processor/summarizer/request.go`
- `pkg/processor/summarizer/execute.go`
- `pkg/processor/summarizer/util.go`
- `pkg/processor/summarizer/processor.go`
- `pkg/model/layout/chunk.go`
- `pkg/model/layout/document.go`
- `pkg/model/layout/search_meta.go`
- `pkg/model/layout/custom_meta.go`
- `pkg/model/layout/xray.go`
- `pkg/model/workflow/workflow.go`
- `pkg/partner/request.go`
- `pkg/partner/workflow.go`
- `server/GroundX/openapi.yml`
- `lambda/GroundX/openapi.yml`

- [x] Add tests that prove the current runtime rejects or drops the proposed
      custom-step shape.
- [x] Add tests that prove `template` round-trips through workflow create/update
      and reaches prompt rendering through workflow/process config, while the
      separate top-level partner template object is not silently accepted as the
      workflow prompt-variable map.
- [x] Add tests for `template` unknown keys, missing required keys, reserved keys,
      invalid value types, payload size, escaping/rendering failures, and fixed
      versus custom prompt behavior.
- [x] Add model support for custom named steps without breaking `StepType`.
- [x] Add storage support for custom chunk/section/document outputs.
- [x] Add persistence and readback tests for old workflows/documents, new custom
      outputs, missing metadata versions, and unknown metadata versions.
- [x] Add processor support for executing allowlisted custom step levels/kinds.
- [x] Add X-Ray output support for custom outputs.
- [x] Add custom section/document output persistence support for the chosen
      storage/readback shape.
- [x] Enforce the chosen field-load validation in the public API/runtime path so
      direct callers cannot bypass the guardrail.
- [x] Reject custom extraction workflow create/update requests with missing,
      unparseable, stale, caller-only, mismatched, or unknown-version
      field-count metadata.
- [x] Add a direct API regression test proving spoofed caller-provided field
      counts cannot bypass the oversized-step guardrail.
- [x] Add direct API regression tests proving mismatched, missing, extra, or
      duplicate route/leaf records cannot bypass field-load validation.
- [x] Update server and lambda OpenAPI mirrors.
- [x] Extend existing `chunk-keys`/`ChunkKeywords` tests instead of replacing
      them.
- [x] Run targeted Go tests for summarizer model, processor, X-Ray, workflow,
      and partner workflow paths.
- [x] Adversarial review: confirm default workflows and existing fixed-step
      overlays still behave exactly as before.

## Task 6: Regenerate And Extend groundx-python

**Repo:** `/Users/benjaminfletcher/git/groundx-python`

**Likely files:**

- Generated files under `src/groundx/types/` after Fern release/regeneration
- Generated workflow clients under `src/groundx/workflows/` after Fern
  release/regeneration
- `src/groundx/extract/prompt/utility.py`
- `src/groundx/extract/prompt/manager.py`
- `src/groundx/extract/classes/groundx.py`
- `src/groundx/extract/classes/document.py`
- `tests/custom/`
- `tests/extract/prompt/test_manager.py`
- `tests/extract/prompt/test_persisted_workflow_extract.py`
- `tests/extract/classes/test_groundx.py`
- `tests/extract/classes/test_document.py`

Status: completed in isolated worktree
`/Users/benjaminfletcher/git/groundx-python-support-custom-workflow-steps-sdk`
on branch `codex/support-custom-workflow-steps-sdk`, final commit `cf85f52`.
Generated SDK output was produced from the upstream Fern/OpenAPI source with
`fern generate --group python-sdk --local --version 3.6.4
--no-require-env-vars` and committed separately from handwritten extract
changes. Verification passed:

- `poetry run pytest tests/custom/test_client.py tests/extract/prompt/test_manager.py tests/extract/prompt/test_persisted_workflow_extract.py -q`
  (`68 passed, 5 subtests passed`)
- `poetry run pytest tests/extract/classes/test_groundx.py tests/extract/classes/test_document.py -q`
  (`20 passed`)
- `poetry run pytest tests/extract -q`
  (`111 passed, 1 skipped, 5 subtests passed`)
- `poetry run pytest -rP -n auto tests/custom tests/extract`
  (`114 passed, 1 skipped`)
- `poetry run mypy .`
  (`Success: no issues found in 219 source files`)
- `poetry run pytest -rP -n auto .`
  (`180 passed, 4 skipped`)
- `OPENSPEC_TELEMETRY=0 npx @fission-ai/openspec@1.3.1 validate support-custom-workflow-steps-sdk --strict`
- `git diff --check`

- [x] Consume generated SDK surfaces from the upstream Fern/OpenAPI change through
      local verification output or the approved SDK release path; do not hand-edit
      generated files.
- [x] Add generated-client serialization tests proving `WorkflowRequest`,
      `WorkflowDetail`, and workflow create/update calls carry `template` and
      custom step config.
- [x] Add hand-written extract tests for YAML custom step metadata.
- [x] Add hand-written extract tests for invalid custom step names, duplicate
      names, fixed-step collisions, case normalization, reserved names, and
      duplicate output destinations.
- [x] Add hand-written extract tests for reserved `workflow:` handling,
      duplicate/conflicting reserved names, and attempted final groups named
      `workflow` failing with a clear migration error.
- [x] Add hand-written extract tests for legacy `slot:` behavior.
- [x] Add extract X-Ray tests for the chosen custom chunk/section/document
      output shape.
- [x] Add document loader tests proving custom X-Ray outputs are available to
      extraction code without breaking `chunkKeywords`.
- [x] Add document-loader/readback tests proving legacy top-level
      `xray.fileSummary` and per-chunk `chunk.fileSummary` behavior remains
      unchanged while custom document outputs use `customDocumentOutputs`.
- [x] Add tests proving custom output route metadata maps the chosen X-Ray path
      back to the final JSON path.
- [x] Ensure `PreparedExtractionYaml.persisted_workflow_extract` preserves
      custom step definitions.
- [x] Ensure mapping input reloads custom step definitions from workflow
      `extract`.
- [x] Add persisted extract version tests for missing, current, unknown, and
      future-version metadata.
- [x] Add SDK-side validation or mirrored errors for oversized executable steps
      according to the Task 2 contract.
- [x] Ensure `PreparedExtractionYaml.persisted_workflow_extract` includes the
      canonical metadata needed for public API/runtime validation to derive or
      verify per-executable-step field counts; optional `field_counts` and
      `schema_hash` remain non-authoritative hints.
- [x] Add tests proving caller-provided field counts that disagree with canonical
      workflow extract metadata fail validation rather than becoming accepted SDK
      output.
- [x] Add tests proving mismatched, missing, extra, or duplicate `outputRoutes`
      and `leafFields` fail validation.
- [x] Add tests proving repeated item/object leaves use wildcard schema paths and
      count once per prompted item leaf.
- [x] Keep `workflow_groups` execution-only.
- [x] Run `poetry run pytest tests/extract -q`.
- [x] Run `poetry run pytest -rP -n auto tests/custom tests/extract`.
- [x] Run `poetry run mypy .`.
- [x] Run `poetry run pytest -rP -n auto .` before PR or release readiness.
- [x] Adversarial review: confirm generated files are not hand-edited directly
      unless the repo guide permits it.

## Task 7: Create Follow-On internal-arcadia-agents Plan

**Repo:** `/Users/benjaminfletcher/git/internal-arcadia-agents`

**Likely files:**

- `prompts/arcadia_manager.py`
- `prompts/yaml.py`
- `tasks/download.py`
- `tasks/agent.py`
- `tasks/save.py`
- `classes/arcadia_agent_request.py`
- `classes/statement.py`
- `classes/extraction_reassembly.py`
- `docs/arcadia-yaml-relationship-algorithm.md`
- `docs/arcadia-yaml-classes/statement.md`
- `docs/arcadia-yaml-classes/meter.md`
- `docs/arcadia-yaml-classes/charge.md`
- co-located tests in `prompts/`, `classes/`, and `testdata/`

Status: current-wave deferral stub is complete at
`/Users/benjaminfletcher/git/internal-arcadia-agents/openspec/notes/support-custom-workflow-steps-deferral.md`.
The remaining Task 7 items are intentionally follow-on work after central
cleanup and closeout, not prerequisites for Task 8.

- [x] During this central plan, create only the deferral stub required by Task 3.
- [ ] After cleanup and closeout of this central planning change, create a new
      repo-owned plan for implementation.
- [ ] The follow-on plan must preserve current reconcile/QA/save behavior except
      `qa_charges`, which is dead legacy and not authorable.
- [ ] The follow-on plan must keep `agent` and `save_agents` internal behind the
      default compatibility adapter.
- [ ] The follow-on plan must define `reconcile_fields`, `qa_fields`, and
      `save_fields`.
- [ ] The follow-on plan must define each new task's behavior, input payload,
      output payload, retry or idempotency assumptions, failure propagation
      behavior, and validation rules.
- [ ] The follow-on plan must name exact failing tests, expected failures,
      implementation steps, verification commands, and commit checkpoints.
- [ ] The follow-on plan must include tests proving missing custom runtime
      metadata uses the current hardcoded workflow steps and current Celery
      graph.
- [ ] The follow-on plan must include tests proving custom output route metadata
      maps from `customChunkOutputs`, `customSectionOutputs`, or
      `customDocumentOutputs` to the final JSON path during reassembly.
- [ ] The follow-on plan must preserve current statement/meter/charge
      relationship logic after reassembly.
- [ ] Run `PYTHONPATH=$PWD pytest prompts classes -q`.
- [ ] Adversarial review: confirm YAML cannot execute arbitrary code or bypass
      final statement/meter/charge business logic.

## Task 8: Update groundx-studio-harness

**Repo:** `/Users/benjaminfletcher/git/groundx-studio-harness`

**Likely files:**

- `skills/groundx-extraction-workflows/SKILL.md`
- `skills/groundx-extraction-workflows/SKILL.public.md`
- `skills/groundx-extraction-workflows/CHANGELOG.md`
- `skills/groundx-extraction-workflows/references/2_schema_design.md`
- `skills/groundx-extraction-workflows/references/3_prompt_pipeline.md`
- `skills/groundx-extraction-workflows/references/4_sdk_integration.md`
- `skills/groundx-extraction-workflows/references/README.md`
- `skills/groundx-extraction-workflows/references/public-docs.md`
- `skills/groundx-extraction-workflows/templates/compile_workflow.py`
- `skills/groundx-extraction-workflows/templates/xray_to_extract.py`
- `skills/groundx-extraction-workflows/templates/validate_workflow_json.py`
- `skills/groundx-extraction-workflows/templates/test_compile_workflow.py`
- `skills/groundx-extraction-workflows/examples/*`
- `skills/groundx-extraction-workflows/evals/evals.json`
- `scripts/tests/test-groundx-extraction-workflows.mjs`
- plugin mirror through `node scripts/sync-plugin.mjs`

Status: completed in isolated worktree
`/Users/benjaminfletcher/git/groundx-studio-harness-support-custom-workflow-steps`
on branch `codex/support-custom-workflow-steps-harness`, commit `b5d8122`.
Plugin payloads were mirrored to `plugins/groundx-studio-harness/` and
`plugins/groundx-agent-harness/`; plugin version bumped to `2.1.6`.
Verification passed:

- `python -m pytest skills/groundx-extraction-workflows/templates/test_compile_workflow.py skills/groundx-extraction-workflows/templates/test_validate_workflow_json.py skills/groundx-extraction-workflows/templates/test_xray_to_extract.py skills/groundx-extraction-workflows/templates/test_imports.py -q`
  (`39 passed`)
- `node scripts/tests/test-groundx-extraction-workflows.mjs`
- `node scripts/tests/test-evals.mjs`
- `node scripts/sync-plugin.mjs --check`
- `node scripts/scans/scan-version-bump.mjs`
- `node scripts/validate.mjs`
- `OPENSPEC_TELEMETRY=0 npx @fission-ai/openspec@1.3.1 validate support-custom-workflow-steps --strict`
- `git diff --check`

- [x] Update harness compiler/templates to emit custom steps only after SDK and
      Go support exists.
- [x] Update X-Ray local aggregation to read `customChunkOutputs`,
      `customSectionOutputs`, and `customDocumentOutputs`.
- [x] Update references so agents know when to use custom steps.
- [x] Update public-docs guidance so agents keep public docs plain and
      SDK-centered.
- [x] Update scanners that currently enforce the old three-slot menu.
- [x] Update evals/examples/changelog language that says only the old three
      slots are supported.
- [x] Update `validate_workflow_json.py` to validate both legacy fixed slots and
      custom-step workflow JSON.
- [x] Mirror the runtime/API hard-fail behavior for custom-step YAML that exceeds
      20 fields per executable workflow step.
- [x] Add compile tests for legacy YAML and custom-step YAML.
- [x] Run `node scripts/validate.mjs`.
- [x] Run `node scripts/sync-plugin.mjs --check` after mirror update.
- [x] Adversarial review: confirm installed skill guidance does not describe
      unimplemented platform behavior.

## Task 9: Update Public Docs

**Repo:** `/Users/benjaminfletcher/git/eyelevel-fern-config`

**Likely files:**

- `fern/pages/extract-data-from-documents.mdx`
- `fern/pages/mcp.mdx`

- [x] Update public docs only after cashbot-go, groundx-python, and harness have
      verified runtime, SDK, and harness behavior.
- [ ] Publish public docs only as the final prerequisite before e2e if published
      docs are required by that e2e path.
- [x] Explain custom workflow steps in plain language without harness internals.
- [x] Explain `template` as workflow-level config.
- [x] Include one legacy YAML example and one custom-step YAML example if the
      final contract supports YAML authoring directly.
- [x] Run `fern generate --docs` as the local docs validation check. Do not
      publish docs until the publish-last gate opens.
      Note: `fern generate --docs --preview --skip-upload --no-require-env-vars
      --no-prompt` reported 0 docs-definition errors and 3 warnings, then failed
      at remote preview publishing with `User does not belong to organization`.
- [x] Adversarial review: confirm public docs explain what engineers do, not
      the internal implementation.

## Task 10: Update ADP POC YAML And Validation

**Repo:** `/Users/benjaminfletcher/git/adp-poc`

Status: completed in isolated worktree
`/Users/benjaminfletcher/git/adp-poc-support-custom-workflow-steps` on branch
`codex/support-custom-workflow-steps-adp` as commit `004f844`. Verification:

- `python -m pytest tests/test_v1_schema_manifest.py -q` (`4 passed`)
- `python -m pytest tests/test_convert_v1_schema_to_yaml.py tests/test_source_review_tools.py -q`
  (`53 passed`)
- Local compile via
  `/Users/benjaminfletcher/git/groundx-studio-harness-support-custom-workflow-steps/skills/groundx-extraction-workflows/templates/compile_workflow.py`
  with
  `PYTHONPATH=/Users/benjaminfletcher/git/groundx-python-support-custom-workflow-steps-sdk/src`
- Local workflow structural validation passed with the same SDK/harness
  worktrees
- `OPENSPEC_TELEMETRY=0 npx @fission-ai/openspec@1.3.1 validate support-custom-workflow-steps --strict`
- `git diff --check`

**Likely files:**

- `workflows/adp_401k_v1/prompt.yaml`
- `workflows/adp_401k_v1/conversion_report.json`
- `tools/convert_v1_schema_to_yaml.py`
- `tests/test_convert_v1_schema_to_yaml.py`
- `tests/test_v1_schema_manifest.py`
- `docs/reference/groundx-extraction-implementation.md`
- `openspec/specs/adp-401k-extraction-yaml/spec.md`

- [x] Add a failing validation that hard-rejects assigning all 159 fields to one
      chunk-level extraction step once custom steps are available.
- [x] Encode the 20-field executable-step limit in the converter or local
      validation tests.
- [x] Confirm ADP validation mirrors, but does not replace, the shared SDK and
      runtime/API 20-field executable-step validation.
- [x] Update the converter to assign coherent final sections or pseudo groups
      to custom steps.
- [x] Preserve the 11 final output sections.
- [x] Keep field count and source-review requirements unchanged.
- [x] Compile the YAML through the updated harness/SDK path.
- [x] Run ADP converter and manifest tests.
- [x] Adversarial review: confirm the ADP migration uses platform features and
      does not hardcode ADP into shared repos.

## Task 11: End-To-End Validation

Status: partially executed and blocked. Evidence is recorded in
`task11-e2e-checkpoint.md`.

- [x] Create or select one legacy YAML and one custom-step YAML.
- [x] Compile both.
- [x] Create/update workflows with both.
- [x] Confirm workflow `extract` preserves authored YAML/custom step metadata.
- [ ] For release readiness, ingest one small representative document for each
      path with live credentials, representative documents, and approval. If any
      are unavailable, record blocked-release status or the explicitly reviewed
      non-live substitute evidence approved by release governance.
- [ ] Retrieve X-Ray and final extract output.
- [ ] Confirm custom step outputs are visible in X-Ray under the chosen shape.
- [x] Confirm custom output route metadata maps the X-Ray/readback value to the
      expected final JSON field.
- [x] Confirm final JSON uses only user-facing YAML group/value names.
- [ ] Confirm old persisted workflow extracts and legacy YAML continue to load or
      fail with the documented compatibility behavior.
- [ ] Confirm direct workflow create/update rejects spoofed, caller-only, or
      mismatched field-count metadata for an oversized custom step.
      Blocked: the deployed API accepted an oversized/spoofed custom-step
      workflow and the test workflow was immediately deleted.
- [ ] Confirm Arcadia default path works for legacy YAML.
- [x] Confirm Arcadia custom field-action implementation is deferred to the
      follow-on `reconcile_fields`/`qa_fields`/`save_fields` plan.
- [ ] Publish SDK/docs if required by the final e2e path, after
      local/runtime/schema/SDK/harness verification passes.
- [ ] Run e2e against the published SDK/docs/runtime artifacts.
- [ ] Confirm downstream repos use `groundx-python >= <released version>` and
      no exact SDK pins were introduced only after published-artifact e2e
      passes.
- [ ] Confirm live deployed-path E2E passed, or record the explicitly reviewed
      non-live substitute evidence approved to unblock release.
- [ ] Adversarial review: confirm the test proves the deployed path, not only
      local compile.

## Task 12: Closeout

- [ ] Update OpenSpec specs in each repo that received code/doc changes.
- [ ] Archive completed OpenSpec plans only after tests pass and PRs merge.
- [ ] Update GitHub/Linear issues with brief human summaries.
- [ ] Record remaining risks and skipped live tests.
- [ ] Confirm the central `groundx-python` planning change was not archived as-is
      with cross-repo durable specs; repo-owned spec deltas were moved to owning
      repo OpenSpec changes before archive.
- [ ] Confirm harness plugin version was bumped when plugin payload changed.
- [ ] Adversarial review: confirm no repo has uncommitted plan/code changes,
      no stale harness plugin mirror, and no docs claiming unavailable behavior.
