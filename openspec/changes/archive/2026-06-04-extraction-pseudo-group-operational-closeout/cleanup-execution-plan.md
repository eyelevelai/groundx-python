# Execution Plan: Pseudo-Group Closeout Cleanup

## Goal

Retire completed SDK-release coordination work now that `groundx[extract]==3.6.0`
has passed the public clean-install import gate, while preserving real remaining
work in the repos that own it.

## Order Of Execution

### 1. GroundX Python

- Confirm `groundx-python` has no remaining implementation or package-release
  tasks for pseudo groups.
- Move any surviving SDK fixture-hardening task into a successor SDK hardening
  plan only if it is still valuable after comparing against existing
  `tests/extract/prompt/test_manager.py` coverage.
- Remove harness-owned and docs-owned checklist rows from the SDK coordinator
  plan once their owning plans carry the work.
- Archive `openspec/changes/extraction-pseudo-group-operational-closeout/` only
  after the coordinator plan contains no unique open work.
- Validate:
  - `git diff --check`
  - `npx -y @fission-ai/openspec@1.3.1 validate --all --json`

### 2. GroundX Studio Harness

- Prune duplicated YAML-parser fixture tasks from
  `openspec/changes/extraction-pseudo-group-release-hardening/tasks.md` when
  the SDK already owns that validation.
- Keep harness-specific coverage only:
  - required SDK version is `groundx[extract]>=3.6.0`
  - harness calls SDK preparation instead of parsing YAML independently
  - split pseudo group route metadata compiles correctly
  - sibling merge pseudo group route metadata compiles correctly
  - pseudo workflow groups do not become final scoring groups
  - one clean-room/sub-agent smoke remains if it is still practical
- Archive the release-hardening plan only if all remaining harness-specific
  checks are complete.
- Leave `openspec/changes/extraction-runner-e2e/` untouched except for the
  already-saved `closeout-execution-plan.md`; this plan is intentionally saved
  for later.
- Validate:
  - `git diff --check`
  - `npx -y @fission-ai/openspec@1.3.1 validate --all --json`
  - `node scripts/validate.mjs`
  - `node scripts/sync-plugin.mjs --check`
  - `node scripts/scans/scan-plugin-bundles.mjs`
  - `node scripts/scans/scan-version-bump.mjs --base origin/main`

### 3. EyeLevel Fern Config

- Keep `publish-extract-data-from-documents` open only for Fern organization
  preview/publish access and URL recording.
- Remove or collapse old SDK-blocker wording so the open task list is only:
  - Fern preview with an account that belongs to the organization
  - optional local docs preview if requested
  - publish/promote
  - record preview or published URL
- Validate:
  - `git diff --check`
  - `fern check`

### 4. Internal Arcadia Agents

- Leave `openspec/changes/extraction-workflow-metadata-runtime-wiring/` open.
- Add a note only if needed that SDK `3.6.0` is available and no longer blocks
  runtime wiring.
- Do not archive this plan until runtime wiring tests and implementation are
  complete.

## GitHub Issue Cleanup

- Confirm `eyelevelai/internal-arcadia-agents#52` is closed with the `3.6.0`
  clean-install evidence.
- Do not close unrelated issues found by broad searches, including Python
  interpreter upper-bound work (`#33`) or API/docs issues.

## Archive Criteria

Only archive a plan when:

- every remaining task is either complete or explicitly moved to a successor
  plan in the owning repo,
- validation for that repo passes after the move,
- no active cross-repo reference still points to the old open plan as the place
  of record.
