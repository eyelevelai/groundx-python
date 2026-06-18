# Change: Clarify Invalid Extraction YAML Errors

Status: proposed

## Problem

`GroundX.create_extraction_workflow(path=...)` and
`GroundX.update_extraction_workflow(path=...)` are the promoted high-level SDK
helpers for valid extraction YAML. When a caller passes invalid in-between YAML,
the SDK can currently surface a low-level preparation error such as
`Expected mapping at [extraction_policy_version]`. That message does not tell
the user whether the top-level key is supported SDK metadata, unsupported
metadata, or a malformed extraction group, nor how to fix the YAML.

This matters because Arcadia YAML may use domain-specific metadata through an
Arcadia metadata-aware preparation path, while public SDK helpers must remain
strict and understandable for generic users.

## Goals

- Keep `create_extraction_workflow(path=...)` and
  `update_extraction_workflow(path=...)` as valid high-level helpers for valid
  YAML.
- Improve invalid authored-YAML errors in the hand-written extract loader so
  unsupported top-level metadata names the offending key and the valid remedies.
- Treat `extraction_policy_version` as supported authored extraction metadata
  so active v1 policy YAML can be loaded by the high-level helpers while still
  preserving the marker in the persisted workflow extract.
- Make sync and async YAML shortcut helpers surface that same actionable error,
  with path context when available.
- Preserve legacy YAML behavior and domain-specific advanced metadata support
  through explicit `prepare_extraction_yaml(..., *_metadata_keys=...)` callers.

## Constraints

- Do not edit Fern-generated SDK files.
- Do not auto-register arbitrary domain-specific metadata for generic SDK
  callers. Only `extraction_policy_version` is promoted to supported SDK
  metadata by this change.
- Do not weaken existing legacy YAML, custom workflow, or persisted workflow
  extract behavior.
