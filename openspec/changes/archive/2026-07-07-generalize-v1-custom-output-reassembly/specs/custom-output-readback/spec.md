## ADDED Requirements

### Requirement: Custom output readback treats records-wrapped rows as generic v1 output

The SDK SHALL treat `_records[]` inside custom output maps as a supported
generic repeated-output container when route metadata is present.

#### Scenario: Records-wrapped rows route to a generic repeated final group

- **GIVEN** a v1 extraction workflow has a custom step with output routes for a
  repeated final group
- **AND** X-Ray contains `customChunkOutputs.<step>._records[]`
- **WHEN** the SDK loads custom outputs through route metadata
- **THEN** it writes one final record per `_records[]` item
- **AND** it does not require the final group to be named `meters` or `charges`.

#### Scenario: Scalar outputs beside records remain routable

- **GIVEN** one custom step output contains both a top-level scalar key and
  `_records[]`
- **AND** route metadata maps the scalar key to a scalar final field
- **AND** route metadata maps keys inside `_records[]` to a repeated final group
- **WHEN** the SDK loads the custom output
- **THEN** both the scalar field and repeated records are present in final output.

#### Scenario: Repeated routes prefer records-wrapped rows

- **GIVEN** a `keys` or `summary` custom step output contains both `_records[]`
  and direct sibling values for the same repeated output keys
- **WHEN** the SDK reassembles repeated route output
- **THEN** `_records[]` is used as the repeated row source
- **AND** direct sibling values do not overwrite or duplicate the records.

#### Scenario: Singular routes ignore records-wrapped rows

- **GIVEN** an `instruct` custom step output contains direct scalar/object keys
  and an unrelated `_records[]` key
- **WHEN** the SDK reassembles singular route output
- **THEN** the direct scalar/object keys are used
- **AND** `_records[]` is not treated as the source for that singular field.

### Requirement: Repeated step kinds create repeated direct final groups

The SDK SHALL treat direct final groups assigned to `keys` or `summary` custom
step kinds as repeated top-level final groups.

#### Scenario: Keys kind marks a top-level repeated final group

- **GIVEN** v1 authored YAML declares a custom step with `kind: keys`
- **AND** a direct final group uses `workflow_step` to assign itself to that
  custom step
- **AND** custom output routes target two-segment paths such as
  `/line_items/description`
- **WHEN** repeated custom output rows are reassembled
- **THEN** the SDK treats the final group as a top-level array
- **AND** one final object is emitted per repeated source row.

#### Scenario: Summary kind also marks a top-level repeated final group

- **GIVEN** v1 authored YAML declares a custom step with `kind: summary`
- **AND** a direct final group uses `workflow_step` to assign itself to that
  custom step
- **WHEN** repeated custom output rows are reassembled
- **THEN** the SDK treats the final group as a top-level array
- **AND** `summary` is not treated as a singular summary object.

#### Scenario: Repeatedness comes from step kind rather than group name

- **GIVEN** a v1 authored workflow declares a direct final group named
  `doctors`, `line_items`, or another non-Arcadia name
- **AND** that group is assigned to a custom step with `kind: keys` or
  `kind: summary`
- **WHEN** repeated custom output rows are reassembled
- **THEN** the SDK emits a top-level array for that group
- **AND** it does not require the group to be named `meters` or `charges`.

#### Scenario: Instruct kind stays singular

- **GIVEN** v1 authored YAML declares a custom step with `kind: instruct`
- **WHEN** custom output routes target two-segment paths under that group
- **THEN** the SDK preserves existing singular-group behavior
- **AND** it does this even if the final group name looks plural.

#### Scenario: Invalid kind fails clearly

- **GIVEN** v1 authored YAML declares an unsupported custom step kind value
- **WHEN** the SDK prepares the extraction YAML
- **THEN** preparation fails with an error naming the custom step and invalid
  kind value.

### Requirement: Repeated custom output is not duplicated by producer-level copies

The SDK SHALL avoid duplicate final rows when section-level or document-level
custom outputs are copied onto multiple chunks in X-Ray.

#### Scenario: Section outputs copied across chunks emit one set of records

- **GIVEN** a v1 workflow has a `section` custom step with repeated output
  routes
- **AND** the X-Ray exposes identical `customSectionOutputs.<step>` data on
  multiple chunks from the same section
- **WHEN** the SDK reassembles custom output
- **THEN** it emits one final row per source record
- **AND** it does not emit duplicate rows for every chunk copy.

#### Scenario: Document outputs copied across chunks emit one set of records

- **GIVEN** a v1 workflow has a `document` custom step with repeated output
  routes
- **AND** the X-Ray exposes identical `customDocumentOutputs.<step>` data on
  multiple chunks or at the document root
- **WHEN** the SDK reassembles custom output
- **THEN** it emits one final row per source record
- **AND** it does not emit duplicate rows for every chunk copy.

### Requirement: Relationship metadata can create nested list output

The SDK SHALL support generic parent/child list relationships through
metadata rather than hardcoded final group names.

#### Scenario: Child records attach to matching parent records

- **GIVEN** a v1 workflow reassembles one parent final group and one child final
  group as arrays
- **AND** `workflow.output_relationships` declares the parent group, child group,
  parent output field, and `match_attrs`
- **WHEN** the SDK reassembles custom output
- **THEN** child records whose present non-blank match fields equal the parent's
  same present non-blank fields are placed in the parent output field
- **AND** the behavior does not depend on final groups named `meters` or
  `charges`.

#### Scenario: Match semantics are Arcadia-compatible

- **GIVEN** relationship metadata declares multiple `match_attrs`
- **AND** parent and child records include extracted-field wrappers, strings,
  integers, floats, blanks, and missing values
- **WHEN** the SDK applies relationship metadata
- **THEN** extracted-field wrappers are compared by their `value`
- **AND** strings compare case-insensitively
- **AND** integers and floats compare by numeric value
- **AND** blank or missing fields do not participate
- **AND** the parent and child only match when they have the same non-empty set
  of present match fields
- **AND** date-style strings are not normalized by the relationship matcher.

#### Scenario: Match attrs without a present key do not match

- **GIVEN** relationship metadata declares `match_attrs`
- **AND** a child and parent both have no non-blank values for those fields
- **WHEN** the SDK applies relationship metadata
- **THEN** the child does not match that parent.

#### Scenario: Unmatched child records are preserved

- **GIVEN** relationship metadata declares `unmatched_child_group`
- **AND** a child record does not match any parent record across all configured
  `match_attrs`
- **WHEN** the SDK applies relationship metadata
- **THEN** the child record remains in the configured unmatched child group.

#### Scenario: Ambiguous child matches fail clearly

- **GIVEN** one child record matches more than one parent record
- **WHEN** the SDK applies relationship metadata
- **THEN** the helper returns a diagnostic that names the relationship and child
  record
- **AND** it does not silently attach the child to an arbitrary parent.

#### Scenario: Chained relationships create arrays inside arrays

- **GIVEN** relationship metadata declares one child group nested under a parent
  group
- **AND** another relationship declares a grandchild group nested under that
  child group
- **WHEN** the SDK applies relationship metadata
- **THEN** the final output can contain a list inside another list item.

#### Scenario: Relationship view is the SDK final output

- **GIVEN** a v1 workflow reassembles parent and child final groups as arrays
- **AND** `workflow.output_relationships` declares how to nest child records
- **WHEN** the SDK reassembles custom output
- **THEN** `final_output` contains the nested relationship-applied view
- **AND** `relationship_output` matches `final_output`
- **AND** `workflow_output` preserves the pre-relationship route output for
  diagnostics.

#### Scenario: Relationship metadata selects the shared v1 output shape

- **GIVEN** a v1 workflow has relationship metadata
- **WHEN** the SDK reassembles custom output
- **THEN** the SDK returns relationship-applied `final_output`
- **AND** the SDK returns matching `relationship_output`
- **AND** generic v1 and Arcadia v1 callers can consume the same SDK
  `final_output` shape.

### Requirement: Relationship metadata is prepared and persisted with workflow metadata

The SDK SHALL preserve `workflow.output_relationships` through prompt
preparation, persistence, reload, and schema hashing.

#### Scenario: Authored relationship metadata persists into workflow extract

- **GIVEN** authored v1 YAML defines `workflow.output_relationships`
- **WHEN** the SDK prepares the extraction workflow
- **THEN** the normalized relationship metadata is included under
  `_groundx_persisted_extract.workflow.output_relationships`
- **AND** the metadata can be reloaded without the original source YAML.

#### Scenario: Relationship metadata changes workflow identity

- **GIVEN** two authored v1 workflows differ only by relationship metadata
- **WHEN** the SDK computes workflow schema hashes
- **THEN** the hashes differ.

#### Scenario: Invalid relationship metadata fails preparation

- **GIVEN** authored v1 YAML defines relationship metadata without a parent
  group, child group, parent output field, or non-empty match attrs
- **WHEN** the SDK prepares the extraction workflow
- **THEN** preparation fails with an error naming the invalid relationship.

#### Scenario: Final-group relationship metadata converts when parent is explicit

- **GIVEN** authored v1 YAML has a child final group with `match_attrs`
- **AND** that child group has existing relationship metadata such as
  `passthrough.from` naming the parent group
- **WHEN** the SDK prepares the extraction workflow
- **THEN** the prepared workflow contains canonical
  `workflow.output_relationships`
- **AND** `parent_group` comes from `passthrough.from`
- **AND** `child_group`, `parent_output_field`, and `unmatched_child_group`
  default to the child group name unless explicitly authored otherwise.

#### Scenario: Final-group match attrs without parent are not guessed

- **GIVEN** authored v1 YAML has a final group with `match_attrs`
- **AND** no direct `workflow.output_relationships` entry or unambiguous parent
  metadata exists
- **WHEN** the SDK prepares the extraction workflow
- **THEN** the SDK does not invent a relationship for that group.

### Requirement: Custom output reassembly helper is a reusable SDK API

The SDK SHALL expose custom-output reassembly through a reusable helper rather
than requiring consumers to depend on `Document` internals.

#### Scenario: Consumers call the SDK helper directly

- **GIVEN** a consumer has an X-Ray mapping or SDK `XRayDocument` object
- **AND** the consumer has a persisted workflow extract containing
  `workflow.custom_steps`, `workflow.output_routes`, and `workflow.leaf_fields`
- **WHEN** the consumer calls `reassemble_custom_outputs(...)`
- **THEN** the helper returns a plain result object with final output and
  diagnostics
- **AND** the result includes a separate relationship output when relationship
  metadata is applied
- **AND** it does not mutate `Document` state or require private `Document`
  methods.

#### Scenario: One implementation serves all v1 callers

- **GIVEN** SDK `Document.load_xray`, harness diagnostic X-Ray reconstruction,
  and an internal service v1 runtime all need to reassemble custom outputs
- **WHEN** they process the same X-Ray custom output and persisted workflow
  extract metadata
- **THEN** they call the same SDK reassembly implementation
- **AND** caller adapters do not duplicate `_records[]`, `keys` / `summary`,
  route-correlation, or section/document dedupe rules.

### Requirement: Existing repeated-output shapes remain supported

The SDK SHALL preserve existing supported custom-output readback shapes while
adding `_records[]` and top-level repeated final-group support.

#### Scenario: Explicit wildcard paths still create repeated nested rows

- **GIVEN** route metadata targets an explicit wildcard path such as
  `/invoice/charges/*/amount`
- **WHEN** custom output contains repeated values
- **THEN** the SDK emits repeated nested rows exactly as before.

#### Scenario: Direct scalar output still routes to scalar final fields

- **GIVEN** custom output contains `customChunkOutputs.<step>.<output_key>`
- **AND** route metadata maps that output key to a scalar final path
- **WHEN** the SDK loads custom outputs
- **THEN** the scalar final field is preserved.
