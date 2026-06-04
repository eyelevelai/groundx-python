# Change: Extraction Pseudo Group Operational Closeout

Status: planned

This is the follow-up plan for work intentionally left open after the SDK,
Fern docs, harness, and Arcadia reassembly implementation chain completed.

## Problem

The pseudo-group YAML contract, docs, harness skill support, and Arcadia
reassembly helper are implemented and the completed plans are archived. Several
operational items still need ownership before the feature should be treated as
release-ready:

- Arcadia runtime wiring still needs a live caller to pass
  `extraction_workflow_metadata_v1` into the reassembly helper.
- Live extraction regression tests need credentials and a deployed workflow.
- The SDK package version containing `prepare_extraction_yaml()` has been
  confirmed as `3.5.9`, and the downstream clean-install import smoke is now
  tracked so release CI does not rely only on development dependencies.
- Generated-source durability must be proven so Fern regeneration does not
  overwrite the hand-written extract SDK surfaces.
- Public docs need a publish/preview pass with Fern organization access.
- Granular hardening fixtures should be expanded after the core behavior is
  stable.
- Existing broad Ruff debt in generated extract files remains separate from the
  pseudo-group change.
- Local untracked `.cgcignore` files should be either intentionally ignored,
  committed where appropriate, or removed.

## Goals

- Coordinate the remaining cross-repo closeout work without reopening completed
  implementation plans.
- Keep each repo responsible for its own executable follow-up tasks.
- Decide release readiness from verified SDK packaging, Arcadia runtime wiring,
  harness compatibility, public docs validation, and live regression evidence.

## Non-goals

- Do not change the pseudo-group YAML syntax in this plan.
- Do not add new pseudo-group behavior without a fresh design review.
- Do not publish docs or plugin bundles without the release-readiness checks in
  this plan.

## Repo-Specific Plans

- Arcadia runtime wiring:
  `/Users/benjaminfletcher/git/internal-arcadia-agents/openspec/changes/extraction-workflow-metadata-runtime-wiring/tasks.md`
- Public docs publish/preview:
  `/Users/benjaminfletcher/git/eyelevel-fern-config/openspec/changes/publish-extract-data-from-documents/tasks.md`
- Harness release hardening:
  `/Users/benjaminfletcher/git/groundx-studio-harness/openspec/changes/extraction-pseudo-group-release-hardening/tasks.md`
