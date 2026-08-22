## MODIFIED Requirements

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
- **AND** leading and trailing string whitespace is removed before comparison
- **AND** internal string whitespace remains significant
- **AND** integers and floats compare by numeric value
- **AND** blank or missing fields do not participate
- **AND** the parent and child only match when they have the same non-empty set
  of present match fields
- **AND** date-style strings are not normalized by the relationship matcher.

Benjamin Fletcher resolved R25b on 2026-08-05: surrounding extraction
whitespace is formatting noise, not identifier identity. The matcher trims only
leading and trailing string whitespace. If trimming creates multiple parent
matches, the tie resolves to the first parent in stable input order: the
2026-08-17 ruling makes an absent `multiple_match_strategy` default to
`first_stable`.

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
- **AND** the behavior equals a declared `multiple_match_strategy: first_stable`
  (2026-08-17 ruling: absence defaults to `first_stable`, the original Arcadia
  tie behavior).

#### Scenario: Ambiguous child matches fail clearly

- **GIVEN** one child record matches more than one parent record
- **AND** the relationship explicitly declares a `multiple_match_strategy`
  other than `first_stable` (rejected at YAML authoring time, but possible on
  an unvalidated runtime packet)
- **WHEN** the SDK applies relationship metadata
- **THEN** the helper returns a diagnostic that names the relationship and child
  record
- **AND** the child stays in the unmatched child group
- **AND** it does not silently attach the child to an arbitrary parent.

#### Scenario: A declared strategy resolves an exact tie

- **GIVEN** one child record matches more than one parent record
- **AND** the relationship declares `multiple_match_strategy: first_stable`
- **WHEN** the SDK applies relationship metadata
- **THEN** the child attaches to the first matching parent in input order
- **AND** no ambiguity diagnostic is emitted.

#### Scenario: Ignored passthrough fields are the only fallback

- **GIVEN** relationship metadata declares `parent_passthrough_attrs` that
  overlap `match_attrs`
- **AND** no parent matches the child on the full populated match-key shape
- **WHEN** the SDK applies relationship metadata
- **THEN** the SDK retries comparison with exactly those passthrough attrs
  removed
- **AND** the child attaches only when exactly one parent survives that retry
- **AND** more than one surviving parent leaves the child unmatched without an
  ambiguity diagnostic
- **AND** `parent_passthrough_attrs` never changes the outcome of the full
  match-key pass
- **AND** removing every match attr, or removing none, performs no retry.

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

- `parents` is an ordered sequence of parent records (mappings), `child` is one
  child record, and `relationship` is the relationship packet.
- The packet is accepted in persisted snake_case or dispatched camelCase
  spelling. `match_attrs`/`matchAttrs`,
  `parent_passthrough_attrs`/`parentPassthroughAttrs`, and
  `multiple_match_strategy`/`multipleMatchStrategy` are the selection-relevant
  fields; snake_case wins when both spellings are present.
- The return value is the frozen dataclass
  `RelationshipParentSelection(parent, ambiguous)`. `parent` is the selected
  parent record object itself — identity-preserving, so a caller can map it back
  to its own domain object — or `None`. `ambiguous` is `True` only for multiple
  exact candidates under an explicitly declared `multiple_match_strategy`
  other than `first_stable`; an absent strategy defaults to `first_stable`
  (2026-08-17 ruling), so undeclared ties select the first parent and are
  never ambiguous.
- The primitive is total: it never raises for unsupported value types.
- Both names are exported from `groundx.extract`.

#### Scenario: Consumers call the selection primitive directly

- **GIVEN** a consumer holds its own parent and child records and a relationship
  packet
- **WHEN** it calls `select_relationship_parent(parents, child, relationship)`
- **THEN** it receives a `RelationshipParentSelection`
- **AND** `parent` is the selected parent record object or `None`
- **AND** `ambiguous` distinguishes an unresolved declared-strategy tie from an
  ordinary no-match
- **AND** the consumer needs no reassembly, X-Ray, or `Document` state to select.

#### Scenario: One primitive serves every workflow

- **GIVEN** pure Arcadia legacy, authored Arcadia v1, authored mechanically
  renamed generic v1, and any other canonical v1 relationship packet
- **WHEN** the SDK selects a parent for a child record
- **THEN** every case is served by the one exported primitive
- **AND** reassembly's `_apply_relationships` delegates to it rather than
  matching inline
- **AND** the selection outcome depends only on the packet's selection-relevant
  fields and the record values, never on group names, final field names,
  workflow identity, or compiler provenance.

#### Scenario: Renamed generic workflows select identically

- **GIVEN** two relationship packets differ only by a one-to-one rename of their
  group names and match-attr names
- **WHEN** the same records are selected through both under that rename
- **THEN** the selected parent and the ambiguity result are the same.

#### Scenario: Retained parent conflicts ride as record siblings

- **GIVEN** a parent record carries retained conflict state for a field the
  passthrough fallback would ignore
- **AND** that state is supplied as the record sibling key `<field>__conflicts`
  holding a list of conflicting values
- **WHEN** the fallback pass would otherwise accept that parent
- **THEN** the SDK rejects that parent and leaves the child unmatched
- **AND** an empty `<field>__conflicts` list does not reject the parent
- **AND** the convention is read-side only: the SDK consumes
  `<field>__conflicts` for selection and defines no policy for writing it.

#### Scenario: Empty routed values retain non-empty conflict siblings

- **GIVEN** a repeated custom-output record has an empty routed field value and
  a non-empty `<field>__conflicts` sibling
- **WHEN** the SDK reassembles custom output
- **THEN** it omits the empty field value
- **AND** it retains the conflict sibling on the same final record
- **AND** fallback parent selection consumes that sibling exactly as it would
  when supplied directly.
