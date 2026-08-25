## ADDED Requirements

### Requirement: Repeated-record identity uses the shared comparison

GroundX Python SHALL use `match_key` for every string component of a generated
repeated-record identity key and `values_match` for every direct identity string
comparison.

#### Scenario: Identity indexes and dedupe share one string rule

- **WHEN** repeated custom output is indexed, partitioned, threshold-matched, or
  deduplicated by configured identity fields
- **THEN** every string key component uses `match_key`
- **AND** direct string equality uses `values_match`
- **AND** existing missing, threshold, shortcut, type, merge, and stable-order
  rules remain unchanged.

#### Scenario: Raw repeated records are retained

- **WHEN** two records merge through the shared comparison
- **THEN** the existing first record and merge rules determine retained output
- **AND** no comparison key appears in output or diagnostics.

## MODIFIED Requirements

### Requirement: Relationship metadata can create nested list output

The SDK SHALL support generic parent/child list relationships through metadata
rather than hardcoded final group names.

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

#### Scenario: Match semantics use the shared comparison

- **GIVEN** relationship metadata declares multiple `match_attrs`
- **AND** parent and child records include extracted-field wrappers, strings,
  integers, floats, blanks, and missing values
- **WHEN** the SDK applies relationship metadata
- **THEN** extracted-field wrappers are compared by their `value`
- **AND** string equality uses `values_match`
- **AND** capitalization and all whitespace are ignored
- **AND** only `{0, o}`, `{1, i, l}`, and `{8, b}` are treated as OCR-confusable
- **AND** integers and floats retain numeric-value comparison
- **AND** blank or missing fields do not participate
- **AND** the parent and child only match when they have the same non-empty set
  of present match fields
- **AND** date-style strings receive no special normalization
- **AND** the first matching parent in stable input order wins.

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

#### Scenario: Missing relationship list groups become empty lists

- **GIVEN** relationship metadata declares parent and child list groups
- **AND** custom output produces no non-empty records for one or both groups
- **WHEN** the SDK applies relationship metadata
- **THEN** the absent relationship groups are treated as empty lists
- **AND** no invalid relationship output diagnostic is emitted.

#### Scenario: Undeclared ties attach to the first stable parent

- **GIVEN** one child record matches more than one parent record
- **AND** the relationship declares no `multiple_match_strategy`
- **WHEN** the SDK applies relationship metadata
- **THEN** the child attaches to the first matching parent in input order
- **AND** no ambiguity diagnostic is emitted
- **AND** the behavior equals a declared `multiple_match_strategy: first_stable`.

#### Scenario: Runtime-only strategy metadata does not change selection

- **GIVEN** one child record matches more than one parent record
- **AND** the relationship explicitly declares a `multiple_match_strategy`
  other than `first_stable`
- **WHEN** the SDK applies relationship metadata
- **THEN** the child still attaches to the first matching parent in input order
- **AND** no ambiguity diagnostic is emitted
- **AND** authoring validation remains responsible for rejecting the foreign
  strategy before persistence.

#### Scenario: A declared strategy resolves a tie

- **GIVEN** one child record matches more than one parent record
- **AND** the relationship declares `multiple_match_strategy: first_stable`
- **WHEN** the SDK applies relationship metadata
- **THEN** the child attaches to the first matching parent in input order
- **AND** no ambiguity diagnostic is emitted.

#### Scenario: Passthrough metadata does not weaken matching

- **GIVEN** relationship metadata declares `parent_passthrough_attrs` that
  overlap `match_attrs`
- **AND** no parent matches the child on the full populated match-key shape
- **WHEN** the SDK applies relationship metadata
- **THEN** the SDK performs no fallback comparison
- **AND** the child remains unmatched
- **AND** `parent_passthrough_attrs` never changes parent selection.

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

### Requirement: Parent selection is one exported SDK primitive

The SDK SHALL expose relationship parent selection as exactly one public
primitive and SHALL use that same primitive for every workflow it reassembles.
No caller and no workflow SHALL get a second matcher, a per-workflow variant, or
a copied selection algorithm.

The public surface is:

```python
from groundx.extract import select_relationship_parent, RelationshipParentSelection

selection = select_relationship_parent(parents, child, relationship)
```

- `parents` is an ordered sequence of parent records, `child` is one child
  record, and `relationship` is the relationship packet.
- The packet accepts persisted snake_case or dispatched camelCase. Only
  `match_attrs` or `matchAttrs` affects parent selection, and snake_case wins
  when both are present.
- The return value is the frozen dataclass
  `RelationshipParentSelection(parent, ambiguous)`. `parent` is the selected
  parent object or `None`. `ambiguous` is always `False` because multiple
  matches select the first parent in stable input order.
- The primitive is total and never raises for unsupported value types.
- Both names are exported from `groundx.extract`.

#### Scenario: Consumers call the selection primitive directly

- **GIVEN** a consumer holds parent and child records and a relationship packet
- **WHEN** it calls `select_relationship_parent(parents, child, relationship)`
- **THEN** it receives a `RelationshipParentSelection`
- **AND** `parent` is the selected parent object or `None`
- **AND** `ambiguous` is `False`.

#### Scenario: One primitive serves every workflow

- **GIVEN** pure Arcadia legacy, Arcadia v1, renamed generic v1, or another
  canonical v1 relationship packet
- **WHEN** the SDK selects a parent
- **THEN** every case uses the one exported primitive
- **AND** reassembly delegates to it rather than matching inline
- **AND** the outcome depends only on `match_attrs`, shared comparison results,
  populated-key shape, and stable parent order.

#### Scenario: Renamed generic workflows select identically

- **GIVEN** two relationship packets differ only by one-to-one group and
  match-attribute renames
- **WHEN** the same records are selected under that rename
- **THEN** the selected parent and ambiguity result are the same.

#### Scenario: Retained parent conflicts do not change selection

- **GIVEN** a parent record carries `<field>__conflicts` for a match field
- **WHEN** the SDK selects a parent
- **THEN** the conflict sibling does not affect comparison
- **AND** selection uses only populated `match_attrs` values.

#### Scenario: Empty routed values retain non-empty conflict siblings

- **GIVEN** a repeated record has an empty routed field and a non-empty
  `<field>__conflicts` sibling
- **WHEN** the SDK reassembles custom output
- **THEN** it omits the empty field value
- **AND** retains the conflict sibling on the same record
- **AND** parent selection ignores that sibling.
