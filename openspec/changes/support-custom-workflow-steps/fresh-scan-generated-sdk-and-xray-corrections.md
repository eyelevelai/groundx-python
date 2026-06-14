# Fresh Scan Corrections: Generated SDK Boundary And X-Ray Runtime

Date: 2026-06-14

## Why This Exists

A fresh scan found two plan risks that must be corrected before closeout:

1. The SDK helper implementation in `groundx-python` currently touches
   generated folders that Fern will overwrite.
2. The custom X-Ray readback contract is not complete until `cashbot-go`
   actually emits `customChunkOutputs`, `customSectionOutputs`, and
   `customDocumentOutputs`, and downstream consumers read those fields.

This file is the central coordination checklist for the corrective work. It is
not a substitute for each repo's implementation plan; it records the cross-repo
contract and the documentation/implementation surfaces that must move together.

## Corrected Execution Plan

1. Update this central OpenSpec plan first.
2. In `groundx-python` SDK helpers, remove all hand edits under generated
   folders:
   - `src/groundx/types`
   - `src/groundx/workflows`
3. Keep handwritten SDK behavior only in handwritten surfaces:
   - `src/groundx/extract/*`
   - `src/groundx/ingest.py`
4. In Fern, define the public API shape that will generate SDK classes and
   workflow client parameters:
   - workflow `template`
   - `customSteps`
   - `outputRoutes`
   - `leafFields`
   - X-Ray `customChunkOutputs`, `customSectionOutputs`,
     `customDocumentOutputs`
5. In `cashbot-go`, implement the runtime and API mirror, not just docs:
   - X-Ray structs expose the custom output maps.
   - X-Ray creation populates those maps from runtime custom-output storage.
   - Existing fixed fields still serialize exactly as before.
   - `server/GroundX/openapi.yml` and `lambda/GroundX/openapi.yml` mirror the
     Fern contract.
6. In `internal-arcadia-agents`, read the new custom X-Ray output attrs in
   metadata-backed reassembly:
   - `customChunkOutputs`
   - `customSectionOutputs`
   - `customDocumentOutputs`
   Legacy fixed attrs remain supported.
7. In `groundx-studio-harness`, keep skill docs, compiler/readback helpers,
   scanners, evals, and generated plugin mirrors aligned with the implemented
   contract.
8. In `adp-poc`, keep ADP-specific YAML/converter/docs aligned with the shared
   SDK/harness contract. ADP must not hardcode shared platform behavior.
9. Run repo-specific verification and adversarial review before claiming
   closeout.

## Repo Coverage Matrix

| Repo / PR | Documentation To Update | Implementation To Update | OpenSpec / Agent Docs To Update |
| --- | --- | --- | --- |
| `groundx-python` plan, PR #10 | This central plan and task list. | No product implementation in the plan PR. | `openspec/changes/support-custom-workflow-steps/*`; this correction file. |
| `groundx-python` SDK helpers, PR #11 | README or SDK docs only if helper examples change. | Move helper logic out of generated `src/groundx/types` and `src/groundx/workflows`; keep code in `src/groundx/extract/*` and `src/groundx/ingest.py`. | Repo-owned `support-custom-workflow-steps-sdk` OpenSpec must state generated files are release/generated-only. |
| `eyelevel-fern-config` docs, PR #12 | Public MDX docs for workflow creation, YAML usage, MCP/workflow docs, and X-Ray/readback if exposed to users. | `fern/openapi.yml` owns generated schema/source API shape. | Repo OpenSpec must keep docs publish gated until runtime/SDK/harness verification. |
| `groundx-studio-harness`, PR #19 | Extraction workflow skill docs, references, examples, scanner messages, eval expectations, and generated plugin mirrors. | Compiler, workflow validation, X-Ray/readback helper, and template/deploy helpers. | Harness OpenSpec plus skill docs must describe only implemented behavior. |
| `internal-arcadia-agents`, PR #66 | Arcadia relationship/runtime docs only where reassembly behavior changes. | Metadata-backed X-Ray reassembly must read custom output attrs plus legacy fixed attrs. | Existing deferral stub remains for future `reconcile_fields` / `qa_fields` / `save_fields`; current-wave plan must not pretend those are implemented. |
| `adp-poc`, PR #1 | ADP reference docs, source-material notes, conversion reports, and workflow docs. | ADP YAML/converter/validation must use shared SDK/harness behavior and preserve final output shape. | ADP OpenSpec documents migration and validation evidence. |
| `cashbot-go` | Human/API docs and mirrored OpenAPI files. Agent docs only if contract guidance changes. | X-Ray structs, X-Ray creation/population, custom-output persistence/readback, workflow validation/runtime as needed. | Cashbot OpenSpec must include failing tests, implementation steps, OpenAPI mirror sync, and adversarial review. |

## Fresh-Scan Checks Before Closeout

- `groundx-python` SDK helper PR has no diff under `src/groundx/types` or
  `src/groundx/workflows` unless that diff is explicitly produced by the
  approved Fern-generated release path.
- `src/groundx/extract/workflows.py` does not import new generated custom
  workflow types for functionality that must survive Fern regeneration.
- `eyelevel-fern-config/fern/openapi.yml` exposes the X-Ray custom output maps
  and workflow custom-step fields.
- `cashbot-go/pkg/model/layout/xray.go` exposes the X-Ray custom output maps.
- Cashbot tests prove custom output maps serialize while fixed X-Ray fields stay
  stable.
- Cashbot `server/GroundX/openapi.yml`, `lambda/GroundX/openapi.yml`, and Fern
  `fern/openapi.yml` agree on public X-Ray/readback shape.
- `internal-arcadia-agents/classes/statement.py` includes the three custom
  X-Ray output attrs in `XRAY_REASSEMBLY_OUTPUT_ATTRS`.
- Arcadia tests cover reading at least one routed value from each new custom
  output attr.
- Harness docs/examples/scanners do not teach deprecated `slot` as the promoted
  custom-step path.
- ADP validation remains shared-contract driven and preserves its final JSON
  shape.

## Audit Status On 2026-06-14

This audit checked the open PR branches named by the user plus the Cashbot PR
created from the support worktree.

| Surface | Current Audit Result | Required Follow-Up |
| --- | --- | --- |
| OpenSpec plan PR #10 | Corrective plan recorded in this file and central `execution-plan.md` / `tasks.md` updated with current pushed commit IDs and remaining release gates. PR #10 is pushed and GitHub checks pass. | Keep PR #10 draft until closeout, then merge or archive according to the final release decision. |
| SDK helpers PR #11 | Fixed at `46e06e4`. No diffs remain under `src/groundx/types` or `src/groundx/workflows`, and `src/groundx/extract/workflows.py` no longer imports generated workflow types. Full SDK pytest, mypy, OpenSpec, and `git diff --check` passed locally. | Merge after review; publish/regenerate generated clients only through the Fern/OpenAPI release path. |
| Fern docs PR #12 | Clean at `5f9650d`. OpenAPI and docs mention `customSteps`, `outputRoutes`, `leafFields`, `requiredTemplateKeys`, and X-Ray custom output maps; the prior merge conflict is resolved. Local Fern/OpenSpec/YAML/diff checks passed. | Keep docs publish gated until runtime, SDK, harness, ADP, and published-artifact e2e checks pass. |
| Studio Harness PR #19 | Revalidated at `64ee14f` after SDK cleanup. Skill docs, compiler/readback helpers, validators, scanners, evals, and generated plugin mirrors reference `workflow_step`, `customSteps`, and custom X-Ray outputs. Local Python, Node, mirror/version, OpenSpec, and diff checks passed. | GitHub marks the PR blocked by external review/check policy; no local validation blocker found. |
| Arcadia PR #66 | Fixed at `edb9b33`. `classes/statement.py` reads `customChunkOutputs`, `customSectionOutputs`, and `customDocumentOutputs`; tests cover chunk, section, and document custom-output reassembly while preserving the future `reconcile_fields` / `qa_fields` / `save_fields` deferral. Full pytest passed locally. | Merge after review; keep the new custom field-action work in a separate follow-on plan. |
| ADP PR #1 | Revalidated at `004f844` after SDK/harness fixes. ADP docs/OpenSpec/YAML reference `workflow_step`, `workflow_output_key`, 20-field validation, and source-material decisions; local compile and structural workflow validation passed with the corrected SDK/harness worktrees. | Merge after upstream runtime/SDK/harness/docs gates are ready; do not hardcode shared platform behavior in ADP. |
| Cashbot PR #1493 | Open at `c4e17a6cf`, base `hotfix-search-dell`. Runtime, X-Ray, tests, and OpenAPI mirror changes for custom output maps are pushed on the hotfix release branch. Targeted Go/OpenSpec/diff checks and local merge simulation against `origin/hotfix-search-dell` passed after removing duplicate rebased OpenAPI `WorkflowTemplate` and `template` entries. GitHub checks are rerunning after retarget. | Let CI finish, then review, merge, and deploy this runtime/API guardrail before published-artifact e2e; full `go test ./...` remains blocked locally by existing repo-wide generated `version.go` and external service/state dependencies. |

## Release Gate

Do not close this central plan until documentation and implementation updates
are present in the relevant repo PRs or explicitly recorded as blocked. Public
SDK/docs publishing remains publish-last: publish only after local/runtime/API,
SDK, harness, and ADP validation have passed and immediately before the
published-artifact end-to-end check.
