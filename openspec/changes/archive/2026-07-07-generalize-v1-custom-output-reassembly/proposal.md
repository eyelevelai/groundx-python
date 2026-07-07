# Change: Generalize V1 Custom Output Reassembly

Status: proposed

## Problem

GroundX custom workflow steps can write repeated model output under
`customChunkOutputs.<step>._records[]`. Arcadia handles this today in its local
runtime adapter, but the SDK's generic `Document.load_custom_outputs()` path
does not treat `_records[]` as a first-class repeated-output shape. That means a
v1 workflow can be valid and still fail or drop data when the consumer is the
generic SDK path instead of Arcadia's local adapter.

Arcadia also currently relies on local runtime knowledge that final groups named
`meters` and `charges` are arrays. That keeps current Arcadia working, but it is
not a generic v1 contract. Generic v1 extraction needs the SDK to understand
which custom workflow steps produce lists without depending on final group names.
It also needs metadata-defined parent/child list relationships so a generic
workflow can produce arrays of objects and arrays inside those objects without
Arcadia-specific code.

The existing step `kind` names are the contract, but the docs and SDK readback
path do not make the output shape clear enough. `kind` is overloaded today: it
selects the backend step family and it is the only existing signal for the
step's output shape. `kind: instruct` produces one flat object. `kind: keys`
and `kind: summary` both produce repeated record streams. The difference
between `keys` and `summary` is the backend step family, not object-vs-list
shape. Generic v1 readback must honor those existing names instead of adding a
second `shape` vocabulary or relying on Arcadia group names.

## What Changes

- Add one SDK-owned generic v1 custom-output reassembly implementation for
  X-Ray/readback custom maps.
- Treat `_records[]` as a supported repeated-output container, not an
  Arcadia-local special case.
- Preserve existing supported direct shapes:
  direct scalar/object outputs, direct list-of-record step outputs, list-valued
  output keys, and explicit wildcard final paths.
- Treat `kind: instruct` as a singular-object step.
- Treat `kind: keys` and `kind: summary` as repeated-record steps.
- Interpret two-segment final paths such as `/line_items/description` as row
  fields when their assigned workflow step is `keys` or `summary`, not when
  the final group has a special name.
- Build readback repeatedness from `workflow.custom_steps[].kind` and route
  metadata; do not require route authors to add a new `shape` field.
- Support generic `workflow.output_relationships` metadata so child list records
  can be matched into parent list records through configured `match_attrs`.
- Preserve, validate, persist, reload, and schema-hash
  `workflow.output_relationships` as first-class v1 workflow metadata.
- Convert existing final-group relationship metadata into
  `workflow.output_relationships` when parent information is unambiguous, so
  existing YAML ergonomics can keep working while runtime uses one matcher.
- Preserve unmatched child records in a configured top-level group and return a
  diagnostic for ambiguous child-to-parent matches.
- Support chained relationships so generic v1 output can contain arrays inside
  arrays.
- Apply relationship metadata into SDK `final_output` when relationships are
  declared, so v1 generic and v1 Arcadia consumers share one primary output
  shape. Preserve `workflow_output` as the pre-relationship debug view.
- Return `relationship_output` as the same relationship-applied view when
  relationships are declared, for callers that already inspect that diagnostic
  key.
- Expose a reusable SDK helper for v1 custom-output reassembly so SDK
  `Document`, harness diagnostics, and internal Arcadia service code all call
  the same implementation.
- Allow callers to adapt their local X-Ray/request objects into the helper's
  public input shape, but do not allow caller-owned `_records[]`, route,
  repeated-row, relationship-matching, or dedupe logic.
- Keep pure legacy extraction YAML supported.
- Keep generated Fern API code untouched; this change lives only in the
  hand-written `src/groundx/extract/` layer and its tests.

## Impact

- Public SDK behavior becomes safer for all v1 custom workflows that emit
  repeated rows.
- This is a v1 shape correction, not a no-op compatibility change for every
  existing v1 fixture. Direct final groups assigned to `kind: keys` or
  `kind: summary` now reassemble as arrays. Existing v1 workflows that relied
  on those direct groups being singular should use `kind: instruct` instead.
- Arcadia can later delete or delegate its local `_records[]` adapter for v1
  paths while retaining true legacy compatibility locally.
- Generic extraction projects can regression-test supported shapes without
  depending on Arcadia code.
- Generic extraction projects can use metadata-defined list relationships for
  parent/child output instead of building local matchers.
- No X-Ray output shape change is required. `cashbot-go` already writes JSON
  array responses under `_records[]`; this change makes SDK readback match that
  producer contract.
- Existing SDK tests or fixtures that expected direct `kind: keys` groups to
  load as singular objects must be updated or converted to `kind: instruct`.

## Affected Consumers

- `internal-arcadia-agents`: should migrate all v1 readback/reassembly to the
  SDK helper after a release, while retaining legacy Arcadia behavior locally.
  The service should support legacy Arcadia, v1 Arcadia, and v1 generic
  extractions through one v1 SDK reassembly path.
- `groundx-studio-harness`: should treat the SDK helper as the canonical
  reference for custom-output readback behavior. Its local X-Ray reconstruction
  path must move to the SDK helper once the fixed SDK is available. Harness may
  load local JSON files and format diagnostic artifacts, but it must not keep an
  independent parser for `_records[]`, `keys`/`summary`, route correlation, or
  section/document dedupe, and it must not implement parent/child matching
  locally.
- Direct `groundx[extract]` SDK users: gain support for repeated custom outputs
  emitted as `_records[]`.

## Backward Compatibility

Legacy-compatible, with an intentional v1 shape correction. Existing pure
legacy YAML remains accepted. Existing v1 workflows keep the current
`instruct`, `keys`, and `summary` kind names. Existing explicit wildcard paths
continue to work. Direct v1 groups assigned to `keys` or `summary` now
reassemble as arrays; workflows that relied on singular direct `keys` or
`summary` output should use `instruct`.

## Open Design Questions

- Exact SDK release version to consume downstream.
