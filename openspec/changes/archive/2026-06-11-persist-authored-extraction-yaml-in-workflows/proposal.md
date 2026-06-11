# Change: Persist Authored Extraction YAML In Workflows

Status: proposed

This repository does not currently have an OpenSpec validation harness. This
change folder is an OpenSpec-style execution artifact for the hand-written
`groundx.extract` SDK work.

## Problem

The SDK can prepare authored extraction YAML into final groups, workflow groups,
route metadata, and separated metadata surfaces. The current workflow extraction
serialization path still returns an execution-only shape. It preserves field and
prompt content needed by GroundX workflow agents, but it drops authored YAML
metadata such as:

- top-level `extraction_policy_version`
- final-group metadata such as `slot`, `final_value_aliases`, `fill_rules`,
  `passthrough_attrs`, `match_attrs`, and `required_any_attrs`
- any future metadata explicitly preserved by callers through the prepared YAML
  helper

That is not enough for downstream systems that reload the YAML from
`workflow.extract`. `internal-arcadia-agents` downloads the YAML from the
workflow extract definition, so sidecar-only metadata is invisible to the live
runtime.

## Goals

- Add an SDK-owned persisted workflow extract representation that preserves the
  authored YAML metadata needed to reload the extraction contract from
  `workflow.extract`.
- Make the preparation path accept both local YAML text and the JSON-serializable
  mapping stored in workflow API `extract`.
- Keep the execution-only workflow group shape available for prompt rendering
  and workflow-agent execution.
- Preserve legacy YAML behavior when no new metadata is present.
- Preserve pseudo/workflow group behavior, final-group-only output shape, route
  metadata, and existing SDK metadata separation.
- Make the persistence path safe for old and new callers by documenting exactly
  which method returns execution-only workflow groups and which method returns
  the authored/persisted workflow extract payload.
- Add regression tests proving the attached Get Choice style YAML metadata
  survives an SDK round trip through the persisted workflow extract payload.

## Non-goals

- Do not move Arcadia business logic into the SDK.
- Do not make sidecar `extraction_workflow_metadata_v1.json` the only durable
  source of truth.
- Do not require a migration for legacy customers using existing mapping-shaped
  SDK YAML.
- Do not preserve arbitrary unknown keys unless the caller has explicitly
  declared them as supported metadata.
- Do not change generated Fern SDK surfaces outside `src/groundx/extract/` and
  `tests/extract/`.

## Handoff Plans

Execute this plan before the harness and Arcadia plans:

1. SDK persistence contract:
   `/Users/benjaminfletcher/git/groundx-python/openspec/changes/persist-authored-extraction-yaml-in-workflows/tasks.md`
2. Harness compiler/deploy/run preservation:
   `/Users/benjaminfletcher/git/groundx-studio-harness/openspec/changes/persist-authored-extraction-yaml-in-workflows/tasks.md`
3. Arcadia reload/runtime consumption:
   `/Users/benjaminfletcher/git/internal-arcadia-agents/openspec/changes/persist-authored-extraction-yaml-in-workflows/tasks.md`

The harness and Arcadia plans should not be closed until SDK tests prove the
persisted workflow extract payload can be parsed back into the same prepared
metadata surfaces.
