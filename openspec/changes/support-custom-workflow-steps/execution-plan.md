# Execution Chain: Support Custom Workflow Steps

This chain is intentionally staged. Do not start implementation before Task 1
and Task 2 produce a reviewed contract and Task 3 produces repo-specific
implementation plans plus the `internal-arcadia-agents` deferral stub.

Current status: Phase 0 discovery, contract, and repo-owned planning artifacts
are complete. Task 4's Fern/OpenAPI schema checkpoint is committed in
`eyelevel-fern-config` on branch `codex/support-custom-workflow-steps-fern`
(`71b7585`), with a follow-up X-Ray response-schema mirror fix committed as
`cf393f5`. Task 5's cashbot-go runtime/API checkpoint is committed on branch
`codex/support-custom-workflow-steps-runtime` as `4e8b0ef6a`. Task 6's Python
SDK checkpoint is committed in isolated worktree
`/Users/benjaminfletcher/git/groundx-python-support-custom-workflow-steps-sdk`
on branch `codex/support-custom-workflow-steps-sdk` as `cf85f52`, with full SDK
pytest, mypy, OpenSpec, and `git diff --check` verification. Task 8's harness
checkpoint is committed in isolated worktree
`/Users/benjaminfletcher/git/groundx-studio-harness-support-custom-workflow-steps`
on branch `codex/support-custom-workflow-steps-harness` as `b5d8122`, with
Python template tests, Node skill/eval gates, plugin mirror/version checks,
full `node scripts/validate.mjs`, OpenSpec, and `git diff --check`
verification. The
`internal-arcadia-agents` current-wave deferral stub is complete; the full
Arcadia `reconcile_fields` / `qa_fields` / `save_fields` implementation plan is
intentionally follow-on work after central cleanup and closeout. The
source-backed trace is recorded in `chunk-keywords-trace.md`, repo-specific
implementation planning blockers are recorded in `repo-plan-blockers.md`, and
Task 9's public docs checkpoint is committed in `eyelevel-fern-config` on branch
`codex/support-custom-workflow-steps-fern` as `c8074b8`, with `fern check`,
docs-definition validation, OpenSpec strict validation, and `git diff --check`
verification. Docs publishing remains gated on Fern org access and the
published-artifact e2e phase. Task 10's ADP migration checkpoint is committed
in isolated worktree
`/Users/benjaminfletcher/git/adp-poc-support-custom-workflow-steps` on branch
`codex/support-custom-workflow-steps-adp` as `004f844`, with ADP manifest,
converter/source-review, local SDK/harness compile, workflow validation,
OpenSpec strict validation, and `git diff --check` verification. Remaining
current-wave execution is end-to-end validation and closeout. Task 11 has a
partial e2e checkpoint in `task11-e2e-checkpoint.md`; release remains blocked
because the deployed API accepted an oversized/spoofed custom-step workflow that
should have been rejected by the Task 5 runtime/API validation.

Fresh-scan correction: see
`fresh-scan-generated-sdk-and-xray-corrections.md`. Before closeout, the plan
must remove hand-written edits from generated `groundx-python` folders, confirm
Cashbot emits the custom X-Ray output maps at runtime, and confirm Arcadia reads
those custom X-Ray attrs in metadata-backed reassembly. The relevant docs,
agent-facing guidance, OpenSpec files, OpenAPI mirrors, SDK helpers, harness
skills, ADP migration artifacts, and implementations must be updated together or
listed as blocked.

Repo-owned Task 3 artifacts, in dependency order:

1. Fern/OpenAPI and public docs:
   `/Users/benjaminfletcher/git/eyelevel-fern-config/openspec/changes/support-custom-workflow-steps/execution-plan.md`
2. Go runtime/API and OpenAPI mirrors:
   `/Users/benjaminfletcher/git/cashbot-go/openspec/changes/support-custom-workflow-steps/execution-plan.md`
3. Python SDK generated and handwritten extract behavior:
   `/Users/benjaminfletcher/git/groundx-python/openspec/changes/support-custom-workflow-steps-sdk/execution-plan.md`
4. Arcadia current-wave deferral stub:
   `/Users/benjaminfletcher/git/internal-arcadia-agents/openspec/notes/support-custom-workflow-steps-deferral.md`
5. Harness compiler, readback, skills, scanners, and plugin mirrors:
   `/Users/benjaminfletcher/git/groundx-studio-harness/openspec/changes/support-custom-workflow-steps/execution-plan.md`
6. ADP migration and validation:
   `/Users/benjaminfletcher/git/adp-poc/openspec/changes/support-custom-workflow-steps/execution-plan.md`

All repo-owned OpenSpec changes validate with their repo-specific change IDs:
`support-custom-workflow-steps` in `eyelevel-fern-config`, `cashbot-go`,
`groundx-studio-harness`, and `adp-poc`, plus
`support-custom-workflow-steps-sdk` in `groundx-python`. The central
`groundx-python/openspec/changes/support-custom-workflow-steps/` change also
validates, but remains a coordination artifact until Task 12 closes or reduces
it.
`internal-arcadia-agents` intentionally has a non-implementation deferral stub
outside `openspec/changes/`, because current-wave Arcadia work has no durable
spec delta or implementation task.

Locked decisions so far:

- Public workflow config uses `customSteps`, separate from legacy `steps`.
- Public `customSteps[]` records contain `name`, `level`, `kind`, optional
  `config`, and optional `requiredTemplateKeys`; custom step `config` uses the
  existing element-targeted workflow step shape but omits or nulls the legacy
  fixed-output `field`.
- Public workflow config uses `outputRoutes` for custom output route records,
  with persisted `workflow.extract.workflow.output_routes` as the canonical
  snake_case source.
- Public workflow config uses `leafFields` for custom leaf-field records, with
  persisted `workflow.extract.workflow.leaf_fields` as the canonical snake_case
  source.
- `outputRoutes` and `leafFields` must match one-to-one on final path, workflow
  group/field, custom step, level, and output key.
- Custom readback uses `customChunkOutputs`, `customSectionOutputs`, and
  `customDocumentOutputs`, including matching page-level chunk paths under
  `documentPages[].chunks[]` when X-Ray includes page chunks.
- Top-level YAML `workflow:` is always reserved for authoring metadata.
- New YAML uses `workflow_step:`; legacy `slot:` remains supported.
- Public `template` follows cashbot-go workflow/process `Process.Template
  *map[string]string`, not the separate partner template object. YAML-authored
  template values live at workflow-level `workflow.template`; custom steps may
  declare `required_template_keys` / public `requiredTemplateKeys`.
- Explicit YAML custom output keys use field-level `workflow_output_key`,
  persisted route metadata uses `output_key`, and public route records use
  `outputKey`.
- One executable workflow step may own at most 20 fields.
- Field-count validation uses canonical `output_routes` and `leaf_fields`, with
  deterministic hash sorting.
- Leaf-field repetition is represented by `isRepeated`/`repetitionScope` in
  public JSON and `is_repeated`/`repetition_scope` in persisted metadata.
- Repeated item leaves use a literal `*` RFC 6901 path segment as the schema
  wildcard, such as `/fees/*/amount`, and count once per prompted schema leaf.
- Reserved template metadata key names are enumerated and apply equally to
  `template` and `requiredTemplateKeys`.
- Arcadia keeps existing reconcile/QA/save behavior except `qa_charges`, which
  is dead legacy.
- New Arcadia `reconcile_fields`, `qa_fields`, and `save_fields` work is a
  follow-on plan after cleanup and closeout of this central plan; the current
  gate requires only an `internal-arcadia-agents` deferral stub.
- SDK/docs publishing is allowed only late, as the final prerequisite for the
  e2e path that requires published artifacts; downstream dependency changes wait
  until that published-artifact e2e passes.

## Phase 0: Discovery And Contract

1. Complete `chunk-keywords-trace.md`.
2. Complete representative section-summary and document-summary traces.
3. Record the public custom-step shape: workflow-level `customSteps`.
4. Record the exact public custom-step item shape and legacy `field` rejection
   inside custom step `config`.
5. Record the public custom output route container: workflow-level
   `outputRoutes`, persisted as `workflow.extract.workflow.output_routes`.
6. Record the public custom leaf-field container: workflow-level `leafFields`,
   persisted as `workflow.extract.workflow.leaf_fields`.
7. Record route/leaf one-to-one validation for `outputRoutes` and `leafFields`.
8. Record the exact leaf-field repetition flags: `isRepeated` /
   `is_repeated`, `repetitionScope` / `repetition_scope`, and allowed
   repetition-scope values `none`, `field`, and `item`.
9. Record repeated-item wildcard final-path semantics for
   `repetition_scope: item`.
10. Record the X-Ray custom output shape for chunk, section, and document
   outputs: `customChunkOutputs`, `customSectionOutputs`, and
   `customDocumentOutputs`, including `documentPages[].chunks[]` paths when
   X-Ray includes page chunks.
11. Record the YAML metadata key for assigning workflow groups to custom steps:
   `workflow_step: <step-name>`.
12. Record the YAML/public/persisted output-key boundary:
   `workflow_output_key`, `outputKey`, and `output_key`.
13. Record the maximum field count: 20 fields per executable workflow step,
   hard-failed by public API/runtime validation and mirrored by SDK, harness,
   and ADP validation.
14. Record the Arcadia runtime graph decision: existing reconcile/QA/save tasks
   remain supported except `qa_charges`, `agent` and `save_agents` remain
   internal compatibility-adapter nodes, and `reconcile_fields`, `qa_fields`,
   and `save_fields` are deferred to a follow-on plan.
15. Record reserved YAML authoring behavior: top-level `workflow:` is always
   reserved and cannot be a final output group.
16. Record custom output route metadata from X-Ray/readback path to final JSON
   path.
17. Record TypeScript feature-support scope and the mandatory TypeScript
    generation smoke coverage: `fern generate --group ts-sdk` must pass.
18. Record downstream release/version gates, including the publish-last sequence
    where SDK/docs publish after local/runtime/schema/SDK/harness verification
    and immediately before the e2e path that requires published artifacts.
19. Record custom step naming, reserved-name, uniqueness, normalization,
    persisted metadata version, and unknown-version behavior.
20. Record how the public API/runtime rejects oversized executable steps for
    direct API users, and how SDK, harness, and ADP validation mirror that rule.
    Define the server-derived or server-verified persisted workflow extract
    metadata field-count source, `leaf_fields` shape, deterministic hash sorting,
    and missing, stale, caller-only, spoofed, or mismatched metadata failures.
21. Record storage, migration, and readback compatibility for custom outputs.
22. Record `template` validation boundaries for unknown keys, required keys,
    reserved keys, invalid value types, payload size, escaping/rendering
    failures, fixed/custom prompt behavior, workflow-level YAML template values,
    `requiredTemplateKeys`, exact reserved metadata names, and required-key
    normalization/collision behavior.
23. Update this OpenSpec change with the final contract.
24. Create valid repo-specific OpenSpec changes or non-OpenSpec implementation
    plans with exact tests, expected
    failures, implementation steps, verification commands, and commit
    checkpoints. For `internal-arcadia-agents`, create only a deferral stub in
    this current wave.
25. Create or select clean branches/worktrees for every current-wave
    implementation repo and record any existing dirty state that must not be
    mixed into this work.
26. Adversarial review.

Review questions:

- Did the trace cover Go runtime storage and not just OpenAPI/Python classes?
- Did the trace cover chunk, section, and document outputs?
- Did the document-output trace distinguish top-level `fileSummary` from
  per-chunk `fileSummary`, and did the contract choose how SDK/Arcadia read
  custom document outputs?
- Is `template` included in the same contract?
- Does the contract preserve legacy fixed steps?
- Does the contract preserve final JSON group shape?
- Can Arcadia reload everything from `workflow.extract`?
- Does the field-load rule hard-fail the 159-field single-step workflow?
- Does reserved `workflow:` behavior fail clearly for any attempted final group
  named `workflow`?
- Does route metadata make the custom output usable for final JSON reassembly?
- Is the direct public route container `outputRoutes` defined with the same
  logical fields as persisted `output_routes`?
- Is the direct public leaf-field container `leafFields` defined with the same
  logical fields as persisted `leaf_fields`?
- Are `outputRoutes` and `leafFields` required to match one-to-one before counts
  are trusted?
- Are leaf-field repetition flags exact and validation-enforced?
- Is repeated item path syntax exact enough to count schema leaves without
  depending on runtime array length?
- Are explicit output keys consistently represented as `workflow_output_key`,
  `outputKey`, and `output_key` at the correct boundaries?
- Are direct API users protected by the same field-load rule as harness users?
- Can a direct API caller with spoofed or caller-only field-count metadata bypass
  the oversized-step guardrail?
- Does the field-count hash name deterministic sort tuples for `custom_steps`,
  `output_routes`, and `leaf_fields`?
- Can the Arcadia contract preserve the current `agent` / `save_agents` default
  graph behavior as internal compatibility-adapter behavior?
- Did the Arcadia contract explicitly classify the existing `qa_charges` branch
  as dead legacy?
- Are repo-owned OpenSpec changes independently valid and archiveable?
- Are `template` validation and rendering failure boundaries explicit, with
  workflow-level template values and step-level required-key declarations kept
  separate, exact reserved metadata names listed, and required-key
  normalization/collisions defined?
- Is the TypeScript SDK generation path proven even if TS feature docs are
  deferred?
- Are branch/worktree and publish-last release gates concrete enough for another
  agent to follow without mixing unrelated work or publishing early?

## Phase 1: API And Runtime Foundation

1. Update Fern/OpenAPI.
2. Update cashbot-go model/load/save/process/X-Ray.
3. Generate or verify SDK generated surfaces from the upstream Fern/OpenAPI
   branch through local verification output or the approved release path.
4. Add mandatory TypeScript generation smoke coverage, or block the Fern schema
   change until the TypeScript generator can consume it.
5. Add generated Python workflow-client serialization tests for `template` and
   custom steps.
6. Add SDK extract YAML support for custom step metadata and persisted reload.
7. Add SDK X-Ray/readback support for `customChunkOutputs`,
   `customSectionOutputs`, and `customDocumentOutputs`.
8. Adversarial review.

Review questions:

- Does Go accept and execute custom steps without enum parse failures?
- Are custom outputs stored and returned in X-Ray?
- Can the SDK parse and expose those custom outputs?
- Can generated workflow clients serialize the new request/response fields?
- Are generated files treated as local verification output or approved
  release-produced files, rather than hand-edited implementation files?
- Do old fixed-step workflows still pass existing tests?
- Does `template` reach prompt rendering?
- Are downstream repos still blocked from bumping dependencies until the
  published-artifact e2e path passes?
- Is SDK/docs publishing sequenced after local/runtime/schema/SDK/harness
  verification and immediately before final e2e?
- Is local SDK generation clearly allowed for verification before public
  publishing?

## Phase 2: Arcadia Runtime

Deferred from this central plan. After cleanup and closeout, create a new
repo-owned plan for `internal-arcadia-agents` that defines and implements
`reconcile_fields`, `qa_fields`, and `save_fields`. During this central plan,
keep only the reviewed deferral stub.

The follow-on plan must:

1. Preserve legacy default behavior.
2. Keep existing reconcile/QA/save tasks supported except `qa_charges`, which is
   dead legacy.
3. Define `reconcile_fields`, `qa_fields`, and `save_fields`.
4. Define each task's input payload, output payload, retry/idempotency
   assumptions, and failure propagation behavior.
5. Add tests for custom output route metadata from X-Ray/readback path to final
   JSON path.
6. Implement workflow step construction from prepared YAML metadata.
7. Implement allowlisted task graph construction.
8. Adversarial review.

Review questions:

- Can YAML name only known task types?
- Are cycles and missing final stages rejected?
- Does the current production graph remain the default?
- Is `qa_charges` excluded as dead legacy?
- Are `reconcile_fields`, `qa_fields`, and `save_fields` defined only in the
  follow-on plan?
- Do custom outputs reassemble into final JSON without leaking workflow group
  names?
- Do statement, meter, and charge relationship rules still run on the final
  reassembled shape?
- Does every authorable task define its input payload, output payload, retry
  behavior, and failure propagation?

## Phase 3: Harness And Public Docs

1. Update harness compiler, X-Ray helper, skill references, scanners, and plugin
   mirror.
2. Mirror the runtime/API hard-fail validation for the chosen field-count limit.
3. Verify harness legacy and custom-step compile paths.
4. Publish public docs in eyelevel-fern-config only after runtime/SDK/harness
   verification, as the final prerequisite before e2e if the e2e path requires
   published docs.
5. Run compile, validation, docs, and plugin mirror gates.
6. Adversarial review.

Review questions:

- Do harness docs describe implemented behavior only?
- Do public docs avoid harness internals?
- Do public docs describe only behavior already verified in runtime, SDK, and
  harness?
- Does oversized custom-step YAML fail rather than warn?

## Phase 4: ADP Migration

Status: completed in isolated worktree
`/Users/benjaminfletcher/git/adp-poc-support-custom-workflow-steps` on branch
`codex/support-custom-workflow-steps-adp` as commit `004f844`.

1. ADP converter/YAML now use 13 custom chunk/instruct workflow steps.
2. The 20-field executable-step rule is mirrored in ADP validation; the largest
   ADP custom step contains 18 fields.
3. ADP YAML compiles through the updated unpublished SDK/harness worktrees.
4. ADP manifest, converter, and source-review tests pass.
5. Adversarial review is recorded in ADP OpenSpec.

Review questions:

- Does ADP preserve the same final 11-section JSON shape? Yes: tests and
  conversion report preserve 11 sections and 159 final fields.
- Does the ADP workflow avoid the 159-field single-slot load? Yes: 13 custom
  steps, max 18 fields per step.
- Is ADP using shared platform behavior instead of hardcoded shared-repo logic?
  Yes for local validation via the updated SDK/harness worktrees; published
  artifact e2e remains in Phase 5.

## Phase 5: End-To-End Proof

Status: partially executed and blocked. See `task11-e2e-checkpoint.md`.

1. Run one legacy YAML path. Completed locally and via live workflow
   create/get/delete.
2. Run one custom-step YAML path. Completed locally and via live workflow
   create/get/delete.
3. Inspect workflow `extract`, X-Ray, and final JSON. Workflow `extract`
   readback and local synthetic X-Ray-to-final-JSON route mapping are complete;
   live X-Ray/final extract remains blocked.
4. Confirm Arcadia legacy path and confirm custom field-action work remains
   deferred to the follow-on plan. Current-wave deferral stub confirmed.
5. Publish SDK/docs if required by the final e2e path. Blocked on publish
   credentials/Fern org access and the deployed-runtime guardrail failure.
6. Run e2e against the published SDK/docs/runtime artifacts. Blocked.
7. Confirm downstream repos use `groundx-python >= <released version>` and no
   exact SDK pins were introduced only after published-artifact e2e passes.
   Blocked until publish and e2e pass.
8. Confirm old persisted workflow extracts and old legacy YAML still load or
   fail with the documented compatibility behavior. Legacy workflow
   create/get/delete passed on the deployed API; broader persisted-workflow
   checks remain blocked until the deployed validation failure is fixed.
9. Confirm the deployed path with live credentials/documents/approval for release
   readiness. Blocked: deployed API accepted an oversized/spoofed custom-step
   workflow.
10. Record skipped live checks only with the approving reviewer, substitute
   evidence, or blocked-release status. Blocked-release status recorded.
11. If published-artifact e2e fails, mark the release failed and fix forward
    with a corrective patch or replacement publication before dependency bumps.
    Current failure is deployed-runtime/API guardrail mismatch.
12. Adversarial review and closeout. Pending after blocker resolution.
