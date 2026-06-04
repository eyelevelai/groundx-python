# Design: Extract YAML Pseudo Groups

## Current Loader Shape

`src/groundx/extract/prompt/utility.py` is the source of truth for YAML loading.
The current flow is intentionally simple:

1. `load_from_yaml(raw_yaml)` calls `yaml.safe_load(raw_yaml)`.
2. The top-level document must be a mapping.
3. Each top-level key is treated as a group.
4. `group_from_mapping()` injects `attr_name` from the key when absent, reads the
   group's prompt and fields, and returns a `Group`.
5. `PromptManager.get_fields_for_workflow()` caches/deep-copies the resulting
   `dict[str, Group]`.
6. `workflow_extract_dict()` serializes that model into the workflow extract
   payload shape.

Pseudo-group preparation must fit before group construction. Once preparation
finishes, existing builders should still see plain mapping-shaped groups, but
there are now two surfaces:

- final data groups: the customer-facing output object
- workflow groups: execution groups sent to GroundX workflow agents

Legacy YAML with no `_pseudo_groups` keeps these surfaces identical.

Important implementation note: the current branch already contains a partial
`prepare_extraction_yaml()` implementation. Phase 1 must reconcile and replace
that partial contract, including old dot-separated routes, old
`group_metadata` / `pseudo_group_metadata` names, old argument names, and current
exports. Treat this as a compatibility cleanup of the existing helper, not a
greenfield addition.

## Shared SDK Helper

Add a small public helper implemented in
`src/groundx/extract/prompt/utility.py` and exported from
`src/groundx/extract/__init__.py` so the SDK, harness, and Arcadia share one YAML
preparation contract:

```python
prepared = prepare_extraction_yaml(
    raw_yaml,
    top_level_metadata_keys={"domain"},
    final_group_metadata_keys={
        "unique_attrs",
        "match_attrs",
        "conflict_attrs",
        "passthrough",
        "pipeline",
    },
    workflow_group_metadata_keys={"slot"},
)
```

The helper returns a simple structure, for example:

```python
@dataclass(frozen=True)
class FinalFieldPath:
    pointer: str
    segments: tuple[str, ...]

    @classmethod
    def parse(cls, pointer: str) -> "FinalFieldPath": ...
    def to_pointer(self) -> str: ...
    def __str__(self) -> str: ...


@dataclass
class PreparedExtractionYaml:
    groups: dict[str, dict[str, Any]]
    workflow_groups: dict[str, dict[str, Any]]
    pseudo_groups: dict[str, dict[str, Any]]
    workflow_field_paths: dict[str, dict[str, str]]
    top_level_metadata: dict[str, Any]
    final_group_metadata: dict[str, dict[str, Any]]
    workflow_group_metadata: dict[str, dict[str, Any]]
```

The stable public import surface should be:

```python
from groundx.extract import FinalFieldPath, PreparedExtractionYaml, prepare_extraction_yaml
```

Responsibilities:

- Parse YAML with duplicate-key detection before PyYAML can silently overwrite.
- Compose `_defs` / `include` into final real groups when those authoring
  helpers are used.
- Keep `groups` limited to final data groups.
- Build `workflow_groups` for GroundX workflow execution:
  - if `_pseudo_groups` is absent, `workflow_groups` is structure-equivalent to
    `groups`
  - if `_pseudo_groups` is present, `workflow_groups` contains explicit pseudo
    groups plus residual final groups containing fields not routed through a
    pseudo group
- Materialize each pseudo group as a normal group-shaped workflow mapping keyed
  by its authored pseudo-group name so workflow-facing callers can access it by
  name exactly as they access a final group in the legacy path.
- Build `workflow_field_paths`, mapping each workflow-group field key back to
  its final-output JSON Pointer, for example
  `{"statement_identity": {"account_number": "/statement/account_number"}}`.
- Parse and validate route pointers with a shared `FinalFieldPath` helper. Route
  strings are the serialized contract for workflow JSON, run artifacts, docs, and
  Arcadia; parsed path segments are an SDK implementation detail.
- `FinalFieldPath.parse()` accepts only valid final-output JSON Pointers,
  normalizes them into decoded path segments, and raises `ValueError` for
  malformed escape sequences or unsupported pointer depth. `to_pointer()` and
  `str(path)` return the escaped JSON Pointer string used in serialized route
  maps.
- Strip authoring-only keys (`_defs`, `_pseudo_groups`, `include`) from final
  groups and workflow groups before `Group` construction.
- Deep-copy composed field definitions so workflow groups and final data groups
  do not share mutable dictionaries or model state.
- Optionally separate caller-provided top-level metadata, final-group/business
  metadata, and workflow-group metadata.
- Resolve caller-provided workflow metadata onto each effective workflow group,
  keyed by workflow group name, so compilers do not have to infer pseudo-group
  override behavior themselves.
- `final_group_metadata_keys` are stripped from real final groups and exposed in
  `PreparedExtractionYaml.final_group_metadata`; they are not inherited by pseudo
  workflow groups. `workflow_group_metadata_keys` are the only metadata keys
  eligible for workflow inheritance/override. A caller that wants a metadata key
  to be workflow-scoped must opt into that explicitly.
- V1 does not expose a standalone `pseudo_group_metadata` surface. Pseudo-group
  declarations are limited to `prompt`, `fields`, and caller-declared workflow
  metadata. If a future consumer needs non-workflow pseudo-group author metadata,
  add an explicit `pseudo_group_metadata_keys` argument and tests then.
- Leave legacy YAML without `_pseudo_groups`, `_defs`, or `include`
  structure-equivalent to today's loader input.

`PreparedExtractionYaml.groups`, `workflow_groups`, and `pseudo_groups` are
deep-copied, YAML-shaped raw mappings. They are intentionally serializable and do
not contain `Group` model instances. `load_from_mapping()` converts a prepared
raw mapping surface into `dict[str, Group]` when model objects are needed.
`PromptManager` owns the parsed `Group` model surfaces used by workflow
serialization and final-data accessors.

`load_from_yaml(raw_yaml)` should continue to return final data groups only.
PromptManager should cache/build both final data groups and workflow groups.
`get_fields_for_workflow()` and `workflow_extract_dict()` should use
workflow groups. Add an explicit final-data accessor, such as
`get_fields_for_data_object()`, for callers that need the final customer-facing
shape. Add a route-map accessor, such as `workflow_field_paths()`, so Arcadia can
reassemble workflow output into the final data object.
Add a workflow metadata accessor, such as `workflow_group_metadata()`, for
workflow compilers that need effective metadata such as `slot`. Add a final
metadata accessor, such as `final_group_metadata()`, for reconcile, dedupe,
conflict, passthrough, pipeline, and other final-data/business logic.
`PreparedExtractionYaml.groups` is also the final field schema handoff for
consumers such as Arcadia that need field-level requiredness or null-policy
signals while reassembling routed workflow output.

The cross-repo serialized handoff artifact should be named and versioned. The
harness should persist an `extraction_workflow_metadata_v1` JSON object alongside
compiled workflow JSON/run artifacts with at least:

- `schema_version`
- source YAML identifier or checksum
- `workflow_field_paths`
- prepared final `groups` or an equivalent final field schema
- `top_level_metadata`
- `final_group_metadata`
- `workflow_group_metadata`

The SDK does not need to write files in v1, but it must expose enough
serializable data for the harness to create this artifact without rebuilding the
YAML contract itself.

## Proposed YAML Contract

Final groups remain the final data object:

```yaml
statement:
  prompt:
    instructions: Extract statement-level fields for the final statement object.
  fields:
    account_number:
      prompt:
        description: The customer account number.
        identifiers: ["Account Number", "Account #"]
        instructions: Return the account number exactly as printed.
        type: str
    bill_start_date:
      prompt:
        description: The billing period start date.
        identifiers: ["Billing Period", "Service From"]
        instructions: Return the billing period start date as YYYY-MM-DD.
        type: str
    total_amount_due:
      prompt:
        description: The final total amount due.
        identifiers: ["Total Amount Due", "Amount Due"]
        instructions: Return the final total amount due as a number.
        type: float

customer:
  fields:
    customer_name:
      prompt:
        description: The customer name as printed.
        identifiers: ["Customer Name", "Name"]
        instructions: Return the customer name exactly as printed.
        type: str

service_address:
  fields:
    street:
      prompt:
        description: The service street address.
        identifiers: ["Service Address"]
        instructions: Return the street address exactly as printed.
        type: str

_pseudo_groups:
  statement_identity:
    prompt:
      instructions: Extract only the statement identity fields.
    fields:
      account_number:
        path: /statement/account_number
      bill_start_date:
        path: /statement/bill_start_date

  statement_totals:
    prompt:
      instructions: Extract only the statement total fields.
    fields:
      total_amount_due:
        path: /statement/total_amount_due

  customer_packet:
    prompt:
      instructions: Extract customer and service-address fields together.
    fields:
      customer_name:
        path: /customer/customer_name
      service_street:
        path: /service_address/street
```

This YAML produces final data groups:

1. `statement`
2. `customer`
3. `service_address`

It produces workflow groups:

1. `statement_identity`
2. `statement_totals`
3. `customer_packet`

It produces a route map:

```python
{
    "statement_identity": {
        "account_number": "/statement/account_number",
        "bill_start_date": "/statement/bill_start_date",
    },
    "statement_totals": {
        "total_amount_due": "/statement/total_amount_due",
    },
    "customer_packet": {
        "customer_name": "/customer/customer_name",
        "service_street": "/service_address/street",
    },
}
```

Arcadia uses that route map after extraction to reassemble:

```json
{
  "statement": {
    "account_number": "...",
    "bill_start_date": "...",
    "total_amount_due": 123.45
  },
  "customer": {
    "customer_name": "..."
  },
  "service_address": {
    "street": "..."
  }
}
```

## Syntax

- `_pseudo_groups` is a reserved top-level mapping.
- Pseudo groups are workflow-only groups. They are functionally like groups for
  prompt/workflow generation, but they do not exist in the final data object.
- Pseudo groups are addressable by their pseudo-group names through
  workflow-facing accessors.
- Pseudo groups may declare:
  - `prompt`
  - `fields`
  - caller-provided workflow metadata such as `slot`, if the caller includes
    that key in `workflow_group_metadata_keys`
- Pseudo groups may not declare arbitrary author metadata in v1. Any pseudo-group
  key other than `prompt`, `fields`, or a caller-declared workflow metadata key is
  rejected.
- Pseudo groups do not declare `include` in v1. `_defs` expands only into final
  groups; pseudo groups route to those already-expanded final fields.
- A pseudo-group field is a mapping with a required `path` pointing to a final
  field path. Paths are JSON Pointers in final-output coordinates, for example
  `/statement/account_number`.
- Path segment escaping follows RFC 6901: `~1` means `/`, and `~0` means `~`.
  Dot characters have no special meaning.
- In v1, a route pointer must resolve to exactly one final field in the current
  flat final-group model: `/<final_group>/<field_key>`. Additional path segments
  are rejected until nested/repeating final schema support exists.
- The pseudo-group field key is the workflow output key for that execution
  group. It may match the final field key or use an alias to avoid collisions.
- Field definitions are inherited from the referenced final field. For v1,
  pseudo-group field entries should not redeclare `prompt`, `fields`, or
  `value`; field-level prompt overrides can be considered later.
- If a pseudo group references fields from one final parent group and has no
  prompt, it inherits shared parent context such as the parent group prompt.
  This lets a split of a large final group keep the parent prompt while still
  giving each split its own workflow group name.
- If a pseudo group references fields from multiple final parent groups, it must
  declare its own mapping-shaped `prompt`.
- `_defs` remains a fields-only authoring helper. Shared prompt text belongs on
  final groups or explicit pseudo groups, not in `_defs`.
- `_defs` and `include` are resolved before pseudo-group routing. A field
  referenced by `path` may come from a direct final group field or from a
  `_defs` include; pseudo groups should not know or care which.
- `prompt` keeps the current mapping-shaped SDK contract; scalar prompt
  shorthand is not supported.

## Workflow Metadata And Slot Resolution

The SDK should not hardcode the meaning or allowed values of `slot`. The harness
owns the slot vocabulary. The SDK should only apply precedence and ambiguity
rules for caller-provided workflow metadata keys, then expose the resolved
metadata in `PreparedExtractionYaml.workflow_group_metadata`.

Workflow metadata is intentionally separate from final-group/business metadata.
For the harness path, `slot` belongs in `workflow_group_metadata_keys`; keys such
as `unique_attrs`, `match_attrs`, `conflict_attrs`, `passthrough`, and
`pipeline` belong in `final_group_metadata_keys` by default. Those final metadata
keys stay attached to the final data group and must not be inherited by pseudo
workflow groups unless a caller deliberately lists one of them as workflow
metadata and adds tests for that workflow-scoped behavior.

For `slot`, the effective workflow metadata rules are:

| Case | Effective result |
| --- | --- |
| No `_pseudo_groups` | Final group workflow metadata applies to that same workflow group. |
| Pseudo group declares `slot` | Pseudo group `slot` wins, even if the parent final group has a different `slot`. |
| Pseudo group omits `slot` and references one final parent with `slot` | Inherit that final parent `slot`. |
| Pseudo group omits `slot` and references multiple final parents with the same non-empty `slot` | Inherit the shared slot. |
| Pseudo group omits `slot` and references multiple final parents with different non-empty `slot` values | Raise `ValueError`; explicit pseudo-group `slot` is required. |
| Pseudo group omits `slot` and references multiple final parents where some have `slot` and some do not | Raise `ValueError`; explicit pseudo-group `slot` is required. |
| Pseudo group omits `slot` and no referenced final parent has `slot` | Leave the workflow group slot unset. The harness may apply a domain profile or raise later. |
| Multiple pseudo groups resolve to the same `slot` | Allowed. Reusing a workflow lane is not an SDK conflict. |
| One pseudo group inherits the parent `slot` and another overrides the same parent `slot` | Allowed. Pseudo groups exist to support this workflow assignment. |

Treat `slot: null` as unset for inheritance. Empty strings should not be given
special SDK meaning; callers or harness validation may reject them as invalid
slot values.

Example:

```yaml
statement:
  slot: chunk-instruct
  fields:
    account_number: ...
    total_amount_due: ...
    late_fee: ...

_pseudo_groups:
  statement_identity:
    fields:
      account_number:
        path: /statement/account_number

  statement_totals:
    slot: chunk-keys
    fields:
      total_amount_due:
        path: /statement/total_amount_due
```

This resolves to:

```python
{
    "statement_identity": {"slot": "chunk-instruct"},
    "statement_totals": {"slot": "chunk-keys"},
    "statement": {"slot": "chunk-instruct"},
}
```

## Workflow Group Construction

When `_pseudo_groups` is absent:

- `groups` equals the final data groups.
- `workflow_groups` equals `groups`.
- `workflow_field_paths` maps each workflow field to its own final-output JSON
  Pointer path.
- `workflow_group_metadata` contains only the caller-declared workflow metadata
  keys extracted from that same final group.

When `_pseudo_groups` is present:

1. Build final `groups` from all real top-level groups.
2. Materialize each authored pseudo group as a group-shaped workflow mapping
   keyed by the pseudo-group name.
3. For each pseudo-group field, validate and deep-copy the referenced final field
   definition into that pseudo workflow group.
4. If the pseudo group references one final parent and does not declare prompt
   context, copy the parent group's prompt context into the pseudo group.
5. Mark each referenced final field path as routed.
6. Build residual workflow groups from final groups with any fields that were not
   routed through a pseudo group.
7. Drop residual final workflow groups with no remaining fields.
8. Populate `workflow_field_paths` for both pseudo groups and residual final
   groups.
9. Populate `workflow_group_metadata` for pseudo groups and residual final
   groups using the metadata precedence and conflict rules above.

This supports both target scenarios:

- Large final groups can be split into several pseudo workflow groups by routing
  subsets of one final group into multiple pseudo groups.
- Small sibling final groups can be processed together by routing fields from
  multiple final groups into one pseudo group.

## Validation

The preprocessor should raise `ValueError` with a useful path for these cases:

- The YAML document contains duplicate mapping keys before composition.
- The YAML document contains a YAML merge key (`<<`). Merge keys have
  overwrite-like semantics and are not supported in v1 unless a later
  duplicate-safe merge implementation validates every merged collision.
- The YAML document contains recursive aliases or any cyclic YAML graph
  structure.
- Top-level `_pseudo_groups` is present but is not a mapping.
- A pseudo group is not a mapping.
- A pseudo group has no `fields` map.
- A pseudo group has an empty `fields` map.
- A pseudo group declares unsupported top-level keys other than `prompt`,
  `fields`, or caller-declared workflow metadata keys.
- A pseudo-group field is not a mapping.
- A pseudo-group field is missing `path`.
- A pseudo-group field path is not a valid JSON Pointer, contains unsupported
  extra segments, or references an unknown final group or field.
- A final field path is routed through more than one pseudo group.
- A pseudo group references multiple final parent groups but does not declare an
  explicit mapping-shaped `prompt`.
- A pseudo group omits `slot` while referencing multiple final parents whose
  effective slot inheritance would be ambiguous.
- A pseudo group declares scalar `prompt:` shorthand.
- A pseudo group declares `include`.
- A pseudo-group field declares unsupported keys such as `prompt`, `fields`, or
  `value`.
- A pseudo group name collides with a final group name.
- A real group or field declares scalar `prompt:` shorthand instead of the
  current mapping-shaped prompt object.
- `_defs` is present but is not a mapping, or a `_defs` fragment declares
  unsupported keys other than `include` and `fields`.
- A `_defs` include is malformed, unknown, cyclic, or creates duplicate final
  field names.

Legacy YAML without `_pseudo_groups`, `_defs`, or `include` must continue to pass
through the helper unchanged except for duplicate-key validation and rejection of
YAML merge keys. Anchors and aliases remain allowed only as ordinary YAML
references; prepared mappings are deep-copied before use so aliases do not create
shared mutable model state. Recursive aliases or any YAML graph that creates a
cycle must raise `ValueError` before composition.

## Implementation Notes

- Add `prepare_extraction_yaml()` and `PreparedExtractionYaml` to the
  `groundx.extract` public export surface. Keep harness-only metadata names as
  caller-provided arguments, not SDK constants.
- Add `final_group_metadata` and `workflow_group_metadata` to
  `PreparedExtractionYaml`. The SDK resolves workflow metadata precedence and
  ambiguity; the harness interprets what metadata values such as `chunk-instruct`
  mean, and Arcadia/business logic consumes final-group metadata from the
  final-group metadata surface.
- Replace direct `yaml.safe_load()` usage inside this loader path with a
  duplicate-key-aware PyYAML loader/constructor. It should use PyYAML only,
  raise `ValueError`, and fail before any duplicate key can be silently
  overwritten.
- Detect and reject YAML merge keys (`<<`) in the duplicate-key-aware loader.
  Do not add partial merge-key support that allows explicit keys to override
  merged keys silently.
- Detect and reject recursive aliases/cyclic YAML object graphs after load and
  before field composition. Ordinary non-recursive anchors and aliases remain
  legal only after the prepared surfaces are deep-copied into independent plain
  mappings.
- Keep the prepared mappings plain Python dictionaries. Do not add a new parser
  or dependency.
- Add `load_from_mapping(groups)` if useful for constructing `Group` objects from
  prepared final groups or workflow groups without a YAML serialization
  round-trip.
- Keep `load_from_yaml(raw_yaml)` returning final data groups only.
- Update `PromptManager` so workflow-facing methods use prepared workflow groups
  while final-data accessors use prepared final groups.
- Add an SDK route-map accessor for Arcadia reassembly.
- Add an SDK workflow metadata accessor for harness workflow compilation.
- Keep `Group`, `ExtractedField`, and workflow serialization behavior unchanged
  unless tests demonstrate a required integration fix.
- Do not silently overwrite fields. The loader must fail fast on duplicate YAML
  keys, duplicate final field names, and duplicate pseudo-group routes.

## Test Strategy

Add focused tests under `tests/extract/prompt/`, following the existing
`unittest.TestCase` convention.

Coverage targets:

- Legacy YAML without `_pseudo_groups`, `_defs`, or `include` produces the same
  `load_from_yaml()` group keys, field keys, prompt values, and
  `workflow_extract_dict()` shape as before the helper.
- A large final `statement` group can be split into two pseudo workflow groups;
  `load_from_yaml()` returns only `statement`, while `workflow_extract_dict()`
  contains the pseudo groups.
- Two small sibling final groups can be routed into one pseudo workflow group.
- Routed final fields are removed from residual final workflow groups.
- Unrouted final fields remain in residual final workflow groups.
- `workflow_field_paths` maps pseudo-group aliases and residual final fields to
  the correct final-output JSON Pointer paths.
- Pseudo groups inherit final field definitions by deep copy.
- A single-parent pseudo group without prompt inherits the parent group prompt.
- Workflow-facing accessors expose pseudo groups by their authored names as
  group-shaped objects, including inherited parent prompt context for
  single-parent splits.
- A multi-parent pseudo group without prompt raises `ValueError`.
- Effective workflow metadata positive cases:
  no-pseudo final-group slot identity, pseudo explicit slot wins, single-parent
  pseudo slot inheritance, multi-parent same-slot inheritance, no-parent-slot
  unresolved metadata, multiple pseudo groups sharing one slot, and mixed
  inherited/overridden pseudo slots from the same parent.
- Effective workflow metadata conflict cases:
  multi-parent pseudo group with different parent slots, and multi-parent
  pseudo group with partially missing parent slots, both without explicit pseudo
  `slot`.
- Unknown final path, duplicate route, malformed `_pseudo_groups`, missing or
  empty pseudo-group `fields`, malformed pseudo field, scalar prompt shorthand,
  unsupported pseudo-group metadata, pseudo field prompt override, and name
  collision with a final group raise `ValueError`.
- `_defs` remains fields-only and can still compose final group fields before
  pseudo group routing.
- Pseudo groups cannot use `include`; tests should prove `_defs` expansion
  happens through final groups before pseudo routing, not directly on pseudo
  groups.
- Duplicate YAML keys raise `ValueError` before composition.
- YAML merge keys raise `ValueError`; anchors and aliases used as ordinary YAML
  references do not create shared mutable state in prepared mappings.
- Recursive aliases or cyclic YAML graphs raise `ValueError`.
- JSON Pointer paths support escaped `~1` and `~0`, reject malformed escape
  sequences, and reject unsupported nested/repeating paths until that schema
  model exists.
- The stable public import
  `from groundx.extract import FinalFieldPath, PreparedExtractionYaml, prepare_extraction_yaml`
  works.

## Verification Gates

Run the narrow gates while iterating:

```sh
poetry run pytest -rP tests/extract/prompt/test_manager.py
poetry run pytest -rP tests/extract/prompt
```

Before handoff to docs, harness, and Arcadia:

```sh
poetry run pytest -rP -n auto tests/extract
poetry run pytest -rP -n auto .
poetry run mypy .
poetry run pyright -p pyrightconfig.json
```

If only `utility.py` and prompt tests change, also run Ruff on the changed files
when available. The required repository gates are pytest, mypy, and Pyright.

For the local `extract-sdk` editor workspace only, also run this non-portable
workspace-level Pyright check when validating Pylance-visible diagnostics across
the symlinked repos:

```sh
npx -y pyright@latest -p /Users/benjaminfletcher/git/extract-sdk/pyrightconfig.json
```
