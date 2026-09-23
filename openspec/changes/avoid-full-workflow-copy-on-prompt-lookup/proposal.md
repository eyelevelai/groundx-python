# Avoid full-workflow copies for prompt lookups

## Why

`PromptManager.group_field`, `group_load`, and `get_prompt` currently call `get_fields_for_workflow`, which deep-copies every cached workflow group. Large extraction tasks repeat singular field lookups thousands of times. The deployed workflow is already cached and pinned by the caller; these copies add local CPU time without protecting the requested value any better.

## What changes

- Keep existing workflow cache and version resolution, but copy only the requested field, group, or prompt for singular accessors.
- Keep whole-workflow getters and their defensive-copy contract unchanged.
- Remove only Arcadia request-scoped caches that duplicate this fix; retain task-scoped workflow identity, field allowlists, role routing, and final-field mapping.
- Verify the protected Arcadia paths and a local replay of the captured large-charge boundary before an SDK release or Arcadia dependency change.

The public method signatures, return types, missing-entry errors, and caller-owned copy behavior do not change. This is a hand-written `src/groundx/extract/` change protected by `.fernignore`; OpenSpec also survives regeneration. Arcadia is the downstream consumer and must adopt a released SDK before removing its compatibility workaround in production. No generated code, customer YAML, or runtime topology changes.

Open questions: none.
