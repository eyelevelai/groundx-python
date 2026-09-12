# AGE-349 Workflow Revision SDK Helper Plan

## Why

Applications and extraction services need to load a saved workflow revision
without rebuilding its settings or falling back to the current workflow. Existing
Python convenience methods already own source selection and raw-YAML submission.

## What Changes

- Extend existing sync/async definition loaders with an optional revision_id.
- Forward optional expected_updated_at through raw-YAML update helpers.
- Preserve server-returned currentRevisionId and result provenance in responses.
- Test the generated revision API together with the preserved helper layer.

## Capabilities

### New Capabilities

- `workflow-revision-sdk-helpers`: exact historical reads and safe updates.

## Impact

Handwritten changes are restricted to .fernignore-protected src/groundx/ingest.py,
src/groundx/extract/, tests/custom/, tests/extract/, and docs. openspec/ is also
protected. Generated clients/types come from Fern, not this plan's handwritten
code. Changes are additive keyword arguments; retain existing defaults and
sync/async behavior. No new dependency or client-side version database is needed.

Internal Arcadia and the Studio Harness consume this release. Generated
TypeScript coverage belongs to the Fern companion. The existing compiler
retirement work remains separate; do not revive or expand local compilation.
Rollback pins the last compatible package, retaining revision-capable consumers
until pinned jobs drain. Package publication is human-owned.
Open design questions: none.

## Delivery boundary

This is a plan-only change. Implementation tasks remain unchecked. The
[producer-owned design](https://github.com/EyeLevel-ai/cashbot-go/blob/backend/age-349-workflow-revision-plan/openspec/changes/age-349-workflow-revision-management/design.md) defines revision identity, persistence,
authorization, restore, and rollout. This companion owns only its repository's
implementation. Changes to that shared contract must update the producer and
consumers together.

Workflow revisions record configuration, not the runtime software build. Coordinate
with AGE-350 runtime provenance without replacing or claiming its implementation.
