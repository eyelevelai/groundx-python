# Generalize V1 Custom Output Reassembly Design

## Goals

- Make v1 custom-output readback generic in the SDK.
- Support `_records[]` wherever route metadata maps custom step outputs to final
  fields.
- Make the existing `workflow.custom_steps[].kind` names drive generic output
  shape: `instruct` is one object; `keys` and `summary` are repeated records.
- Stop relying on final group names like `meters` or `charges` to decide array
  behavior.
- Support nested list output through explicit route paths and metadata-defined
  parent/child list relationships.
- Provide a generic SDK relationship helper so downstream services can match
  child records into parent records through metadata instead of hardcoded group
  names.
- Preserve legacy YAML and existing explicit wildcard repeated paths.
- Provide a regression matrix that catches breaking changes across legacy,
  Arcadia v1, and generic v1 shapes.

## Non-Goals

- Do not change the GroundX platform response shape.
- Do not change `cashbot-go` producer behavior.
- Do not remove legacy YAML support.
- Do not move Arcadia-specific meter completeness, charge dedupe, passthrough,
  reconcile, QA, or final rendering policy into the SDK.
- Do not add Arcadia-specific group names to the SDK. Generic relationship
  support must use metadata such as parent group, child group, target field, and
  match fields.
- Do not edit generated Fern code.

## Ownership Boundary

SDK-owned generic v1 mechanics, implemented once:

- Reads `customChunkOutputs`, `customSectionOutputs`, and
  `customDocumentOutputs`.
- Applies `workflow.output_routes` and `workflow.leaf_fields`.
- Supports direct output keys and `_records[]`.
- Creates repeated rows from route metadata.
- Uses the assigned custom step kind to detect top-level repeated groups.
- Provides the reusable helper that performs the above behavior for SDK,
  harness, and Arcadia v1 consumers.
- Tests legacy-safe loading, generic v1 groups, Arcadia-shaped v1 groups, and
  backend `_records[]` output.
- Owns all parsing and correlation rules for `_records[]`, direct list output,
  `keys`/`summary` repeatedness, explicit wildcard paths, and section/document
  duplicate suppression.
- Owns generic metadata-driven list relationship mechanics when relationship
  metadata is supplied: attach child list records to parent list records when
  all configured match fields match, preserve unmatched child records according
  to metadata, and support chained relationships for arrays inside arrays.

Harness-owned behavior:

- YAML authoring guidance and examples.
- Compile/deploy/run scripts and local workflow ergonomics.
- Prompt wrapper generation and pre-registration validation.
- Scoring, comparison, and local business-logic utilities.
- Loading local `xray.json` and `workflow.json.extract` artifacts, invoking the
  SDK helper, and writing diagnostic artifacts.
- Local business-logic and scoring utilities after SDK reassembly.
- No independent `_records[]`, `keys`/`summary`, route-correlation, or
  section/document dedupe parser after the fixed SDK is available. If a
  temporary local implementation remains before the SDK release, it must have
  parity tests against SDK behavior for `_records[]`, `keys`, `summary`,
  section-level copies, and document-level copies.

Internal Arcadia service-owned behavior after SDK reassembly:

- Pure legacy YAML compatibility.
- V1 service orchestration for both Arcadia utility-bill workflows and generic
  v1 extraction workflows.
- Arcadia statement/meter/charge policies.
- Meter acceptance rules.
- Arcadia-specific charge dedupe and meter/charge business policy.
- Supplying v1 relationship metadata that maps the utility-bill parent/child
  relationship into the SDK's generic relationship helper.
- Final Arcadia JSON rendering.
- Reconcile, QA, and save chain behavior.

The architecture should avoid three independent readback implementations. The
SDK helper is the source of truth for generic v1 output mechanics. SDK
`Document`, harness, and internal Arcadia service code may have thin call sites
that load local data, normalize object attributes, and handle post-result
behavior, but they must not independently own `_records[]`, direct-list,
`keys`/`summary`, route correlation, or section/document dedupe rules.

## Relationship Metadata And Nested Lists

Generic v1 readback has two stages:

1. Reassemble scalar fields and list groups from custom output routes.
2. Apply optional relationship metadata to place child list records inside
   parent list records.

These stages must produce a clear primary output and debug view:

- `final_output`: the SDK v1 output. When relationships are declared, this is
  the relationship-applied view.
- `workflow_output`: the pre-relationship route output for diagnostics.
- `relationship_output`: the same relationship-applied view when relationships
  are declared, preserved for callers that inspect the relationship key.

Arcadia v1 and generic v1 consumers use the same SDK `final_output` contract.
Child records that do not match any parent remain in the configured
`unmatched_child_group`.

`workflow.output_relationships` creates relationship context and selects the
relationship-applied view as the SDK `final_output`. `workflow_output` remains
available as the flat pre-relationship debug view, and `relationship_output`
mirrors `final_output` for callers that inspect that key directly.

The SDK should support relationship metadata under the prepared workflow extract,
for example:

```yaml
workflow:
  output_relationships:
    - parent_group: meters
      child_group: charges
      parent_output_field: charges
      match_attrs:
        - meter_number
        - provider_name
        - service_type
      unmatched_child_group: charges
```

The names above are generic. `meters` and `charges` are only example authored
group names; the same shape must work for `claims` and `line_items`, `accounts`
and `transactions`, or any other v1 extraction.

Relationship rules:

- `parent_group` and `child_group` name final groups already reassembled by
  custom output routes.
- `parent_output_field` names the list field to create inside each matching
  parent object.
- `match_attrs` lists the fields that may identify a parent/child match.
  Matching uses Arcadia-compatible semantics:
  - unwrap extracted-field objects such as `{"value": ...}` before comparing;
  - ignore missing, `None`, and blank-string values;
  - strings compare case-insensitively;
  - integers and floats compare as numeric values;
  - date-style strings are not normalized by the SDK matcher;
  - the parent and child must have the same non-empty set of present match
    fields, and every present field value must match.
- `unmatched_child_group` preserves children that do not match any parent. This
  keeps Arcadia-style account charges possible without hardcoding that behavior.
- Relationships may be chained: a child group can itself be the parent of
  another child group, which supports arrays inside arrays.
- Relationship application must be deterministic. If one child matches multiple
  parents, the helper must return a diagnostic instead of silently choosing.

This is not Arcadia business logic in the SDK. It is a generic "match child rows
to parent rows by configured fields" primitive. Arcadia v1 can use the same
generic metadata, for example `charges.match_attrs` plus
`charges.passthrough.from: meters`, while keeping legacy behavior and
Arcadia-specific dedupe, requiredness, passthrough, reconcile, QA, and rendering
rules local.

## Relationship Metadata Lifecycle

`workflow.output_relationships` is durable v1 workflow metadata. It must travel
through the same SDK preparation and persistence path as `workflow.output_routes`
and `workflow.leaf_fields`:

- YAML authoring may define `workflow.output_relationships` directly.
- SDK prompt preparation validates and normalizes each relationship entry.
- `src/groundx/extract/prompt/utility.py` includes `output_relationships` in
  the custom workflow authoring key set and persisted key set.
- Persisted workflow extracts include `workflow.output_relationships` under
  `_groundx_persisted_extract`.
- Workflow reload uses the persisted relationship metadata without requiring
  the original YAML file.
- Schema hashing includes normalized relationship metadata so changing a
  parent group, child group, output field, or match field changes the workflow
  identity.
- Invalid relationship metadata fails preparation clearly before extraction is
  run.

Required validation:

- `parent_group`, `child_group`, `parent_output_field`, and `match_attrs` are
  required.
- `match_attrs` must be a non-empty list of field names.
- `unmatched_child_group` is optional, but when present must be a field name.
- Relationship groups are names, not Arcadia roles. The SDK must not require
  names such as `meters` or `charges`.

The SDK may also accept explicitly supplied normalized relationship metadata at
the helper boundary for staged migrations, but persisted workflow metadata is
the target contract.

## Relationship Metadata Conversion

The SDK should also provide one generic conversion path from existing final-group
relationship metadata into canonical `workflow.output_relationships`. This lets
existing authoring ergonomics survive while runtime uses one SDK matcher.

Conversion rules:

- Direct `workflow.output_relationships` wins and is preserved as authored after
  normalization.
- A final group can be converted into a child relationship when its metadata has
  non-empty `match_attrs` and enough parent information to be unambiguous.
- Existing harness-style metadata supplies parent information through
  `passthrough.from`. In that case:
  - `child_group` is the final group carrying `match_attrs`;
  - `parent_group` is `passthrough.from`;
  - `parent_output_field` defaults to the child group name;
  - `unmatched_child_group` defaults to the child group name.
- If a group has `match_attrs` but no unambiguous parent group, the SDK must not
  guess. The caller must author `workflow.output_relationships` directly or pass
  explicit normalized relationship metadata.
- Arcadia's charge-to-meter relationship is caller-supplied through generic
  final-group metadata. The SDK does not infer the parent group from names like
  `meters` or `charges`.

The conversion helper must only produce relationship metadata. It must not run
matching, dedupe, passthrough field copying, charge policy, or final rendering.
Converted final-group metadata creates relationship context only; SDK
`final_output` remains the single v1 output contract.

## Step Kind Semantics

The SDK should use the existing `workflow.custom_steps[].kind` value to
determine the custom step's output shape. This does not add a new `shape`
field and does not rename any existing kind:

```yaml
workflow:
  custom_steps:
    - name: statement_fields
      level: chunk
      kind: instruct
    - name: line_item_fields
      level: chunk
      kind: keys
    - name: meter_fields
      level: chunk
      kind: summary

statement:
  workflow_step: statement_fields

line_items:
  workflow_step: line_item_fields

meters:
  workflow_step: meter_fields
```

Rules:

- `kind: instruct` means the step produces one flat object.
- `kind: keys` means the step produces zero or more flat record objects.
- `kind: summary` also means the step produces zero or more flat record
  objects. It is a repeated-record kind, not a singular document summary.
- The difference between `keys` and `summary` is which backend fixed step
  family runs. It is not a final JSON shape distinction.
- When a `keys` or `summary` step returns `_records[]` and routes point to
  `/line_items/description` or `/meters/meter_number`, the SDK writes one
  object per record under that final group.
- Existing explicit wildcard paths such as `/invoice/charges/*/amount` remain
  supported and do not require any final-group metadata.
- The SDK must reject invalid kind values clearly.
- The SDK must not infer repeated groups from names such as `meters`, `charges`,
  `doctors`, or `line_items`.

This keeps Arcadia's desired final shape possible without making `meters` and
`charges` special SDK names.

The readback helper must join each route back to its step metadata. If a route
does not directly carry `kind`, build a `step_name -> kind` index from
`workflow.custom_steps`. Repeatedness comes from that effective kind plus the
route path, not from the final group name. The effective kind is a derived
lookup used during preparation and readback; it is not a new authored or
persisted `shape` field.

`leaf_fields.is_repeated` currently reflects explicit wildcard paths. That value
must not be the only source of truth for v1 readback because direct
`keys`/`summary` routes such as `/line_items/description` are repeated even
without a `*`. Implementations may add derived repeatedness to normalized
metadata, but the durable contract is: consumers can derive effective
repeatedness from `workflow.custom_steps[].kind` plus `output_routes`, and no
authored `shape` field is required.

## Reassembly Algorithm

For each custom output route:

1. Locate the source map by `route.output_map`.
2. Locate the step output by `route.step_name`.
3. Determine whether the route is repeated:
   - a `final_path` containing `*` is repeated;
   - a two-segment `final_path` assigned to `kind: keys` or `kind: summary` is
     repeated;
   - all other routes are singular.
4. For repeated routes, locate values in this order:
   - if `step_output._records` is a list, read each record's
     `route.output_key` or `route.workflow_field`;
   - if the step output itself is a list, read each row's key or scalar value;
   - if `step_output[route.output_key]` or `step_output[route.workflow_field]`
     is a list, read one item per row;
   - otherwise treat the direct object/scalar value as one record.
5. For singular routes, locate the direct `route.output_key` or
   `route.workflow_field` value first and preserve today's scalar/object
   behavior. Singular routes must not consume `_records[]`.
6. Correlate values from the same repeated record index into one final row.
7. Write through `route.final_path`.
8. If the route path has `*`, use the explicit wildcard path.
9. If the route path has two segments and the route's assigned step kind is
   `keys` or `summary`, treat it as a repeated top-level final group.
10. If neither repeated condition applies, write a scalar/mapping field as
    today.
11. After route reassembly, read `workflow.output_relationships` when present
    and apply the nested relationship view to `final_output`. Preserve
    `workflow_output` as the pre-relationship debug view.

The helper must preserve top-level scalar outputs that appear beside `_records[]`
in the same custom step.

For `keys` and `summary`, direct object outputs remain supported as a single
record. Records-wrapped output and list output produce one row per record.
For `instruct`, two-segment routes stay singular even if the group name happens
to be plural.

## Source Identity And Duplication

The helper must process each producer-level output once:

- Chunk-level custom outputs are processed once per chunk.
- Section-level custom outputs may be copied onto each chunk in the section by
  the producer. Reassembly must identify the section source and avoid emitting
  duplicate rows for every chunk copy.
- Document-level custom outputs may also appear on multiple chunks. Reassembly
  must identify the document source and avoid duplicate document rows.

Source identity must be explicit:

- Chunk identity: output level, chunk id or chunk ordinal, output map, step
  name, route id or final path, and record index.
- Section identity: output level, section id when available, otherwise the
  stable section/page span plus output map, step name, route id or final path,
  and record index.
- Document identity: output level, document id when available, otherwise a
  single document sentinel plus output map, step name, route id or final path,
  and record index.

Section and document copies attached to multiple chunks must collapse to one
source identity. Distinct records from the same section or document must stay
distinct by record index.

Reading strategy:

- For repeated routes, prefer `_records[]` or direct list output when present.
  A direct object is treated as one record.
- For singular routes, use the direct value and keep today's scalar/object
  behavior.
- `_records[]` plus scalar siblings is a defensive readback case that must
  preserve both shapes, even if not every producer currently emits that mix.

## Helper API Contract

The SDK should expose one reusable helper with a stable import surface:

```python
from groundx.extract.custom_outputs import (
    CustomOutputReassemblyResult,
    reassemble_custom_outputs,
)
```

The helper contract:

- Inputs: a plain X-Ray mapping or SDK `XRayDocument`-like object, plus a
  persisted workflow extract mapping that contains `workflow.custom_steps`,
  `workflow.output_routes`, and `workflow.leaf_fields`.
- Output: `CustomOutputReassemblyResult` with `final_output: dict`,
  optional `relationship_output: dict | None`, `workflow_output: dict`,
  `diagnostics: list`, and enough source metadata for callers to explain which
  route, step, output map, output level, source identity, and record index
  produced each value.
- Relationship support: the helper reads generic `workflow.output_relationships`
  metadata when present and returns the nested relationship-applied view in
  `final_output` and `relationship_output`. Callers may also pass the same
  normalized relationship specs explicitly if their local metadata source has
  not yet been persisted
  into the workflow extract.
- Behavior: pure function; no live API calls, no prompt rendering, no mutation
  of `Document`, and no dependency on private `Document` subclass internals.
- Consumers: `Document.load_xray()` uses the helper internally, harness
  diagnostic X-Ray reconstruction imports it when the released SDK is available,
  and Arcadia v1 calls it before Arcadia-specific business logic.
- Errors: invalid route metadata and unsupported shapes are returned as
  diagnostics or raised as clear value errors before data is silently dropped.

Implementation may use small normalization adapters inside the SDK to convert
SDK objects and plain JSON mappings into one canonical sequence of custom output
containers. Those adapters are not alternate reassembly implementations: they
must not interpret `_records[]`, decide repeatedness, correlate fields, or dedupe
section/document copies. That logic lives in the one SDK reassembly core.

## Regression Matrix

SDK tests must cover:

- pure legacy YAML still loads and behaves as before;
- generic v1 scalar custom outputs;
- generic v1 explicit wildcard repeated outputs;
- generic v1 top-level `kind: keys` direct groups;
- generic v1 top-level `kind: summary` direct groups;
- `_records[]` repeated rows;
- `_records[]` plus sibling scalar outputs from one step;
- direct list-of-record step outputs;
- list-valued output keys;
- a plural-looking direct group whose step is `instruct` stays singular;
- a generic direct group not named `meters` or `charges` becomes repeated when
  assigned to `kind: keys` or `kind: summary`;
- generic relationship metadata nests child records under matching parent
  records without using Arcadia group names;
- unmatched child records remain in the configured unmatched child group;
- a child that matches multiple parents returns a diagnostic instead of being
  silently attached;
- chained relationships can create an array inside an array;
- `final_output` is relationship-applied when `relationship_output` is produced;
- prompt preparation preserves, persists, reloads, validates, and hashes
  `workflow.output_relationships`;
- section-level outputs copied across chunks do not duplicate rows;
- document-level outputs copied across chunks do not duplicate rows;
- repeated routes prefer `_records[]` over direct sibling values, while singular
  routes ignore `_records[]` and read direct scalar/object values;
- the current SDK direct `kind: keys` singular fixture is either updated to the
  corrected repeated shape or changed to `kind: instruct` if it is meant to stay
  singular;
- invalid custom step kind;
- missing route metadata does not silently fabricate final rows.

Consumer tests must cover:

- current Arcadia v1 shape with `meter_fields.kind: summary` and
  `charge_fields.kind: keys`;
- pure legacy Arcadia YAML through the local legacy path;
- a v1 generic extraction through the internal Arcadia service path, proving the
  service does not require final groups named `meters` or `charges`;
- a v1 generic extraction with relationship metadata proves the internal service
  can opt into SDK-backed parent/child list matching without Arcadia group-name
  checks;
- harness local X-Ray reconstruction delegates to the SDK helper after the
  fixed SDK is available and keeps only local file loading/result formatting.
  Any temporary duplicate logic must have parity tests for `_records[]`, `keys`,
  `summary`, section-level copies, and document-level copies.

## Implementation Surface

Hand-written SDK paths:

- `src/groundx/extract/classes/document.py`
- a new or existing hand-written helper under `src/groundx/extract/`
- `src/groundx/extract/prompt/utility.py` for final-group metadata support
- tests under `tests/extract/`

The change is inside `.fernignore`-protected paths.

Downstream parity path:

- `groundx-studio-harness/skills/groundx-extraction-workflows/templates/xray_to_extract.py`
  must delegate to the SDK helper after the harness pins or can import the fixed
  SDK. Track that in a required harness OpenSpec change; harness should retain
  local file loading, artifact naming, scoring, and business-logic calls, but not
  custom-output parsing rules.
- `internal-arcadia-agents/classes/statement.py` should delegate all v1
  custom-output mechanics to the SDK helper after the SDK release. Legacy
  no-metadata Arcadia behavior remains local. V1 Arcadia and v1 generic
  workflows should enter the same SDK-backed reassembly path before service
  reconcile/QA/business rules run.

## Release And Migration

1. Ship the SDK behavior and tests first.
2. Release a new `groundx[extract]` version.
3. Update `internal-arcadia-agents` to depend on that SDK version.
4. Move Arcadia v1 custom-output parsing to the SDK helper.
5. Keep Arcadia legacy fallback local.
6. Include a release note that this is legacy-compatible but intentionally
   corrects v1 direct `keys` and `summary` groups to arrays.
