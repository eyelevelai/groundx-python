## ADDED Requirements

### Requirement: Arcadia custom step support keeps legacy defaults

Arcadia custom workflow-step and runtime-graph support SHALL preserve the
current production default when custom runtime metadata is absent.

#### Scenario: Arcadia defaults to current production graph

- **GIVEN** Arcadia YAML without custom runtime graph metadata
- **WHEN** Arcadia starts an extraction
- **THEN** it uses the current production chord/chain graph
- **AND** statement, meter, and charge reconciliation behavior remains
  unchanged

#### Scenario: Arcadia existing graph tasks have safe execution contracts

- **GIVEN** Arcadia YAML with allowlisted runtime graph metadata
- **WHEN** Arcadia validates and executes the graph
- **THEN** the initial authorable task vocabulary is limited to reviewed
  existing business actions: `reconcile_charges`, `reconcile_meters`,
  `reconcile_statement`, `qa_meters`, `qa_statement`, `save_charges`,
  `save_meters`, and `save_statement`
- **AND** every authorable task has a documented input payload, output payload,
  retry or idempotency assumption, and failure propagation behavior
- **AND** the existing `qa_charges` code path is classified as dead legacy and
  is not authorable
- **AND** invalid payload handoff, unsupported graph shapes, cycles, and missing
  required save or finalization stages fail before arbitrary task execution

#### Scenario: Arcadia custom graph can represent the production default

- **GIVEN** the current production graph includes the internal `agent` task and
  `save_agents` aggregation behavior
- **WHEN** the custom graph vocabulary is finalized
- **THEN** the contract defines a compatibility adapter that preserves the
  current default graph exactly when custom runtime metadata is absent
- **AND** `agent` and `save_agents` remain internal graph nodes
- **AND** the default graph can be represented, tested, and compared without
  weakening existing statement, meter, or charge behavior

### Requirement: Arcadia custom field actions are planned separately

Arcadia SHALL add `reconcile_fields`, `qa_fields`, and `save_fields` as custom
field actions only through a follow-on plan created after cleanup and closeout
of this central planning change.

#### Scenario: Central plan records only a deferral stub

- **GIVEN** this central planning change is preparing current-wave implementation
  work
- **WHEN** repo-specific planning gates are reviewed
- **THEN** `internal-arcadia-agents` has a deferral stub rather than a current
  implementation plan
- **AND** the stub records preserved legacy reconcile/QA/save behavior
- **AND** the stub records that `qa_charges` is dead legacy and not future
  authorable vocabulary
- **AND** the stub records that `reconcile_fields`, `qa_fields`, and
  `save_fields` require a follow-on repo-owned plan after central closeout

#### Scenario: Custom field action work is deferred to a new plan

- **GIVEN** this central plan is being closed out
- **WHEN** Arcadia custom field action work is ready to begin
- **THEN** a new repo-owned plan defines `reconcile_fields`, `qa_fields`, and
  `save_fields`
- **AND** that plan defines each action's behavior, input payload, output
  payload, retry or idempotency assumptions, failure propagation behavior, and
  required `internal-arcadia-agents` implementation changes
- **AND** this central plan does not silently start that implementation work
