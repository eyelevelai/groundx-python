# Spec delta — extract-yaml (fix-persisted-workflow-derivation)

## MODIFIED Requirements

### Requirement: Field paths preserve final_path verbatim

`workflow_field_paths` SHALL carry each route's `final_path` verbatim, including `*` tokens —
they are load-bearing vocabulary for the SDK's own row routing (field-level lists such as
`/group/list_field/*/sub`). Consumers with narrower path contracts (the Arcadia reassembly
parser's 2-segment group/field pointers) SHALL normalize at THEIR export boundary
(internal-arcadia-agents `workflow_reassembly_metadata`), never in the shared derivation.
(Fresh-scan P1/P2: the earlier "SDK dialect is 2-segment" model was falsified by the SDK's own
row-routing tests — both dialects legitimately contain `*`.)

#### Scenario: starred routes survive derivation untouched

- **GIVEN** a persisted workflow whose `output_routes[].final_path` values include `*` tokens
- **WHEN** `prepare_extraction_yaml` derives `workflow_field_paths`
- **THEN** every derived path equals its route's `final_path` byte-for-byte

### Requirement: Readers do not verify writer hashes

The persisted-workflow reader SHALL NOT compare the stored `schema_hash` against any recompute
(cross-implementation hash comparison is the proven false-positive: distinct canonicalizations
disagree over identical structures). The stored hash is writer-owned and opaque to readers.
Read-time integrity SHALL be structural validation of the stored metadata; a canonical hash MAY
be recomputed for runtime use but SHALL never gate loading.

#### Scenario: either dialect loads without hash errors

- **GIVEN** a workflow persisted in the harness or SDK dialect with its writer's hash
- **WHEN** the persisted metadata is loaded for runtime use
- **THEN** no schema-hash comparison occurs and loading succeeds

#### Scenario: structural corruption still fails

- **GIVEN** a persisted workflow whose routes reference undefined steps or malformed targets
- **WHEN** the persisted metadata is loaded
- **THEN** structural validation raises a descriptive error
