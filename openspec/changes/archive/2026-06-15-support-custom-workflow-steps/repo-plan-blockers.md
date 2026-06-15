# Repo-Specific Planning Closeout Checklist

This file records the repo-specific planning requirements that Task 3 needed to
satisfy. Task 3 planning is now complete and reviewed; implementation remains
blocked only on creating or selecting the clean implementation branch/worktree
named by each repo-owned plan and saving the untracked planning artifacts.

Locked decisions:

- Workflow config uses `customSteps`, separate from legacy `steps`.
- Custom output readback uses `customChunkOutputs`, `customSectionOutputs`, and
  `customDocumentOutputs`.
- Top-level YAML `workflow:` is always reserved.
- New YAML uses `workflow_step:`; legacy `slot:` remains supported.
- `template` follows cashbot-go workflow/process `Process.Template
  *map[string]string`, not the partner template object.
- One executable workflow step may own at most 20 fields.
- Arcadia keeps existing reconcile/QA/save actions except `qa_charges`, which is
  dead legacy. `agent` and `save_agents` stay internal.
- `reconcile_fields`, `qa_fields`, and `save_fields` belong in a follow-on
  `internal-arcadia-agents` plan after this central plan is cleaned up and
  closed out.
- SDK/docs publishing is the final prerequisite before the e2e path that
  requires published artifacts; downstream dependency bumps wait until that e2e
  passes.
- Route metadata records `workflow_group`, `workflow_field`, `final_path`,
  `step_name`, `level`, `output_map`, `output_key`, and `readback_path`.
- Public workflow config carries route records as `outputRoutes`; persisted
  metadata stores them as `workflow.extract.workflow.output_routes`.
- Public workflow config carries leaf-field records as `leafFields`; persisted
  metadata stores them as `workflow.extract.workflow.leaf_fields`.
- `outputRoutes` and `leafFields` must match one-to-one on final path, workflow
  group/field, custom step, level, and output key; missing, extra, duplicate,
  stale, or mismatched route/leaf metadata fails before hashing or execution.
- Explicit output keys are authored in YAML as field-level
  `workflow_output_key`, persisted as `output_key`, and exposed in public JSON
  route records as `outputKey`.
- Public `customSteps[]` records contain `name`, `level`, `kind`, optional
  `config`, and optional `requiredTemplateKeys`; custom step `config` reuses the
  existing element-targeted workflow step shape but must omit or null the legacy
  fixed-output `field`.
- Custom step names are lower snake case, globally unique, fail on
  auto-normalization ambiguity, and cannot collide with fixed aliases or
  reserved workflow/runtime names.
- `workflow.metadata_version: 1` is current. Unknown/future custom workflow
  metadata versions fail closed; missing workflow metadata is legacy fallback
  only when no custom workflow metadata is present.
- Public API/runtime field counts are server-recomputed from canonical
  `workflow.extract.workflow.output_routes` and
  `workflow.extract.workflow.leaf_fields`. Caller-provided `field_counts` and
  `schema_hash` are non-authoritative hints, and hash arrays use deterministic
  identity sorting.
- Leaf-field repetition uses explicit `is_repeated` and `repetition_scope`
  metadata, exposed publicly as `isRepeated` and `repetitionScope`.
- Repeated item leaves use a literal `*` RFC 6901 path segment as the schema
  wildcard, such as `/fees/*/amount`, and count once per prompted schema leaf.
- Template config is `map[string]string`, allows extra keys, blocks reserved
  names and invalid types/sizes, stores YAML-authored values at workflow-level
  `workflow.template`, declares required keys through step metadata, validates
  required keys with the same normalization/rules as template keys, and keeps
  existing fixed-prompt optional placeholder behavior.
- Reserved template key names are enumerated by the central workflow-config spec
  and must be reused for both `template` and `requiredTemplateKeys`.

## `/Users/benjaminfletcher/git/eyelevel-fern-config`

- Plan covers `customSteps`, `template`, the three custom output maps, and
  the 20-field validation contract in OpenAPI/Fern.
- Plan requires TypeScript generation smoke coverage.
- Plan defines the publish-last SDK/docs gate and the downstream lower-bound
  dependency sequence.

## `/Users/benjaminfletcher/git/cashbot-go`

- Plan chooses the Go model change that supports `customSteps` without
  breaking fixed `StepType`/`FieldType` behavior.
- Plan identifies storage and X-Ray/readback work for `customChunkOutputs`,
  `customSectionOutputs`, and `customDocumentOutputs`.
- Plan keeps fixed document-summary `fileSummary` behavior unchanged while
  routing custom document outputs through `customDocumentOutputs`.
- Plan enforces the 20-field limit from canonical `workflow.extract` schema
  and route metadata, rejecting spoofed/caller-only counts.
- Plan exposes workflow/process `template` matching `Process.Template
  *map[string]string` and avoid confusing it with the partner template object.

## `/Users/benjaminfletcher/git/groundx-python`

- Plan consumes generated SDK surfaces from upstream Fern/OpenAPI.
- Plan implements always-reserved `workflow:`, `workflow_step:` assignment,
  legacy `slot:` compatibility, custom step naming rules, persisted metadata
  versioning, and custom output route metadata.
- Plan parses `customChunkOutputs`, `customSectionOutputs`, and
  `customDocumentOutputs` while preserving fixed top-level and per-chunk
  `fileSummary` behavior.
- Plan mirrors the 20-field limit and emits/verifiably preserves the canonical
  metadata needed by public API/runtime validation.

## `/Users/benjaminfletcher/git/internal-arcadia-agents`

- Current central plan records the Arcadia decisions but defers implementation.
- The current Task 3 gate needs only a deferral stub for this repo, not a full
  implementation plan for `reconcile_fields`, `qa_fields`, and `save_fields`.
- Follow-on plan will use the three custom output maps for reassembly route
  metadata.
- Follow-on plan will keep `agent`/`save_agents` internal behind the default
  compatibility adapter.
- Follow-on plan will treat `qa_charges` as dead legacy.
- Follow-on plan will define `reconcile_fields`, `qa_fields`, and `save_fields`
  behavior, payloads, retry/idempotency assumptions, failure propagation, tests,
  and implementation steps.

## `/Users/benjaminfletcher/git/groundx-studio-harness`

- Plan waits for SDK/runtime support for `customSteps` and custom output
  maps before teaching or validating them as implemented behavior.
- Plan mirrors the 20-field executable-step limit and public API/runtime
  error behavior.
- Plan keeps installed skill guidance behind real platform behavior.

## `/Users/benjaminfletcher/git/adp-poc`

- Plan uses `workflow_step:` assignment and the 20-field executable-step
  limit.
- ADP implementation remains sequenced after the updated harness/SDK compiler
  path exists.
- Plan preserves the 11 final ADP output sections while splitting the 159
  fields across platform-supported custom executable steps.

## Task 11 E2E Blocker

- Local legacy/custom compile and live workflow create/get/delete checks passed.
- Release e2e is blocked because the deployed API accepted an oversized/spoofed
  custom-step workflow that assigned all 159 ADP routes to one custom step while
  spoofing a low `field_counts` value.
- The created negative-test workflow was deleted and a cleanup scan found no
  remaining `codex-e2e-support-custom-workflow-steps-*` workflows.
- Continue only after the runtime/API artifact with Task 5 field-count
  validation is deployed or e2e is pointed at an approved equivalent deployed
  environment.
