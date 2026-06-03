# Change: Extract YAML Pseudo Groups

Status: planned

This repository does not currently have an OpenSpec validation harness. This
change folder is an OpenSpec-style execution artifact for the hand-written
`groundx.extract` SDK work.

## Problem

Extraction YAML top-level groups represent the final data object being
extracted. That final data shape must stay stable for customers and downstream
systems.

Workflow execution has a different concern: agent load. A final group with more
than roughly 20 fields should be split into smaller workflow execution groups so
dedicated GroundX workflow agents can process the fields reliably. Conversely,
two sibling final groups with fewer than roughly 10 fields each may be better
processed together by one workflow agent.

We need YAML support for pseudo groups: workflow-only groups that behave like
groups for prompt/workflow generation but do not exist in the final data object.
The final reassembly from pseudo-group extraction output back into the final
data shape is owned by `internal-arcadia-agents`.

Workflow-facing SDK surfaces must expose pseudo groups by their authored names
the same way they expose normal groups, while final-data surfaces must continue
to expose only the customer-facing final groups.

## Goals

- Add deterministic YAML preparation for reserved `_pseudo_groups`.
- Preserve final data groups as the source of truth for the output object.
- Produce workflow execution groups from pseudo groups plus any final-group
  fields not routed through pseudo groups.
- Support both large-final-group splitting and small-sibling-group merging.
- Make pseudo groups addressable by name as group-shaped workflow objects.
- Preserve shared parent context, such as a final group's prompt, when a pseudo
  group splits fields from one parent group and does not declare its own
  replacement context.
- Expose a reassembly map from workflow group field keys to final data paths so
  `internal-arcadia-agents` can rebuild the final object.
- Preserve legacy extraction YAML behavior when `_pseudo_groups` is absent.
- Preserve `_defs` as fields-only reusable authoring fragments, not prompt or
  execution-group containers.
- Produce clear validation errors for malformed pseudo groups, unknown field
  paths, duplicate routing, duplicate YAML keys, scalar `prompt:` shorthand, and
  unsupported metadata placement.
- Add focused unit coverage under `tests/extract/` without live network calls or
  new runtime dependencies.
- Stage public documentation, harness, and Arcadia reassembly updates after the
  SDK behavior is implemented and tested.

## Non-goals

- No cross-file imports, globbing, environment interpolation, or package-level
  YAML include system.
- No change to the final data-object shape unless the authored final groups
  change.
- No pseudo groups in final extraction output, scoring output, or customer-facing
  data contracts.
- No reassembly implementation in `groundx-python`; SDK exposes the route map,
  while `internal-arcadia-agents` owns reassembly.
- No reusable prompt text inside `_defs`; shared prompt context belongs under
  real final groups or explicit pseudo groups.
- No scalar `prompt:` shorthand. `prompt` keeps the current mapping-shaped SDK
  contract.
- No mandatory migration for legacy customers. Existing extraction YAML without
  `_pseudo_groups`, `_defs`, or `include` remains valid.
- No public documentation, harness skill, or Arcadia code edits in this repo.
  Those are tracked by the handoff plans below.

## Handoff Plans

Execute these plans in order from the main SDK plan:

1. SDK implementation:
   `/Users/benjaminfletcher/git/groundx-python/openspec/changes/extract-yaml-group-fragments/tasks.md`
2. Public documentation:
   `/Users/benjaminfletcher/git/eyelevel-fern-config/openspec/changes/document-extraction-workflow-walkthrough/tasks.md`
3. Harness extraction skill and workflow guide:
   `/Users/benjaminfletcher/git/groundx-studio-harness/openspec/changes/extraction-yaml-fragments-and-howto/tasks.md`
4. Arcadia reassembly:
   `/Users/benjaminfletcher/git/internal-arcadia-agents/openspec/changes/extraction-pseudo-groups-reassembly/tasks.md`

The documentation, harness, and Arcadia plans must not be treated as complete
until SDK tests prove the final YAML contract, workflow-group shape, route map,
and error semantics.
