# extraction-workflow-convenience Specification

## Purpose
TBD - created by archiving change add-extraction-workflow-convenience-methods. Update Purpose after archive.
## Requirements
### Requirement: Python SDK exposes first-class extraction definition loaders

The Python SDK SHALL expose hand-written methods for loading extraction
definitions from authored YAML and from existing workflow IDs without requiring
callers to work with generated workflow response internals.

#### Scenario: Load extraction definition from YAML path

- **GIVEN** a local extraction YAML file
- **WHEN** a caller invokes `GroundX.load_extraction_definition(path=...)`
- **THEN** the SDK reads the file as UTF-8 YAML
- **AND** prepares it through the same extraction YAML preparation path as
  `prepare_extraction_yaml(...)`
- **AND** returns an `ExtractionDefinition`
- **AND** the returned definition exposes the persisted `extract` payload,
  workflow template, custom steps, output routes, leaf fields, and underlying
  prepared metadata for advanced inspection
- **AND** the base SDK package remains importable without loading optional
  extraction dependencies until this method is called
- **AND** `GroundX.load_extraction_definition_from_yaml(path=...)` remains
  available as an explicit source-specific alias

#### Scenario: Load extraction definition from explicit YAML text or mapping

- **GIVEN** in-memory extraction YAML or a YAML-shaped mapping
- **WHEN** a caller invokes `GroundX.load_extraction_definition(...)`
  with exactly one YAML/prepared source argument and no `workflow_id`
- **THEN** the SDK returns the same `ExtractionDefinition` shape
- **AND** passing zero or multiple YAML/prepared sources fails with a clear
  `ValueError`
- **AND** raw string YAML is passed through `yaml_text`, not ambiguously through
  a bare positional string
- **AND** `mapping` defaults to authored YAML-shaped semantics

#### Scenario: Load extraction definition from explicit workflow extract mapping

- **GIVEN** a persisted or execution-only workflow `extract` mapping
- **WHEN** a caller invokes `GroundX.load_extraction_definition(...)`
  with `mapping=...` and `mapping_kind="workflow_extract"`
- **THEN** the SDK treats the mapping as an existing workflow extract payload
- **AND** preserves the extract mapping exactly
- **AND** sets `prepared=None` when authored YAML metadata is unavailable
- **AND** does not guess `workflow_extract` from dict keys because simple
  authored YAML mappings and simple execution-only extract mappings can look
  identical

#### Scenario: Workflow template values are string-preserving

- **GIVEN** authored YAML whose workflow template contains placeholder-style
  keys such as `{{LANGUAGE}}` and `{{LANGUAGE_UNKNOWN}}`
- **WHEN** the SDK loads the extraction definition
- **THEN** the placeholder keys are preserved exactly as string keys
- **AND** an empty-string value for `{{LANGUAGE_UNKNOWN}}` is preserved
- **AND** non-string template values fail with a clear `ValueError` naming the
  offending template key

#### Scenario: Load extraction definition from workflow ID

- **GIVEN** an existing GroundX workflow ID whose workflow contains extraction
  config
- **WHEN** a caller invokes `GroundX.load_extraction_definition(workflow_id=...)`
- **THEN** the SDK fetches the workflow through the generated workflow client
- **AND** extracts the workflow `extract` mapping and workflow-level extraction
  settings
- **AND** returns an `ExtractionDefinition` compatible with create/update
  helpers
- **AND** preserves top-level workflow response fields such as `template`,
  `custom_steps`, `output_routes`, `leaf_fields`, `chunk_strategy`,
  `section_strategy`, and `steps` when present
- **AND** falls back to persisted workflow metadata under `extract["workflow"]`
  only when the corresponding top-level workflow response field is absent
- **AND** if the workflow has no extraction config, the SDK raises a clear error
  naming the workflow ID
- **AND** `GroundX.load_extraction_definition_from_workflow(workflow_id)`
  remains available as an explicit source-specific alias

#### Scenario: Consolidated loader applies workflow-ID precedence

- **GIVEN** a caller wants to load an extraction definition
- **WHEN** they provide `workflow_id` plus any YAML/prepared source such as
  `path`, `yaml_text`, `mapping`, or `prepared`
- **THEN** `GroundX.load_extraction_definition(...)` loads from `workflow_id`
- **AND** the SDK does not read or validate the lower-priority YAML/prepared
  source
- **AND** if `workflow_id` is absent, passing zero or multiple YAML/prepared
  sources fails with a clear `ValueError`
- **AND** `mapping_kind` is valid only when `mapping` is the selected
  YAML/prepared source
- **AND** `request_options` is valid only when `workflow_id` is the selected
  source

#### Scenario: Workflow-loaded definition does not fake authored metadata

- **GIVEN** an existing GroundX workflow whose `extract` mapping does not
  contain `_groundx_persisted_extract`
- **WHEN** a caller invokes
  `GroundX.load_extraction_definition_from_workflow(workflow_id)`
- **THEN** the SDK returns an `ExtractionDefinition` that preserves create/update
  payload fields
- **AND** the definition has `prepared=None`
- **AND** docs state that authored YAML inspection metadata is unavailable for
  such workflow-loaded definitions

#### Scenario: Base SDK import does not require extract extras

- **GIVEN** a Python environment with `groundx` installed without the `extract`
  extra
- **WHEN** a caller imports `groundx`, `GroundX`, or `AsyncGroundX`
- **THEN** the import succeeds
- **AND** non-extraction client methods remain usable
- **AND** base imports do not import `groundx.extract` or representative
  `groundx[extract]` optional dependency modules
- **AND** calling an extraction definition method fails with an actionable
  install hint such as `pip install groundx[extract]`

#### Scenario: Hand-written custom tests survive SDK regeneration

- **GIVEN** the SDK repo uses `.fernignore` as the hand-written boundary
- **WHEN** this change adds a new hand-written test under `tests/custom`
- **THEN** `.fernignore` protects the `tests/custom` test surface before the
  test is added
- **AND** the plan does not rely on unprotected hand-written files surviving
  Fern regeneration by accident

#### Scenario: Async definition loaders have parity

- **GIVEN** an async GroundX client
- **WHEN** a caller invokes
  `AsyncGroundX.load_extraction_definition(...)`,
  `AsyncGroundX.load_extraction_definition_from_yaml(...)`, or
  `AsyncGroundX.load_extraction_definition_from_workflow(...)`
- **THEN** the async methods accept the same source arguments as the sync
  methods
- **AND** workflow-ID loading awaits the generated async workflow call
- **AND** both methods return `ExtractionDefinition`

### Requirement: Python SDK exposes extraction workflow create/update helpers

The Python SDK SHALL expose hand-written convenience helpers that create and
update extraction workflows from `ExtractionDefinition` or authored extraction
YAML without requiring callers to manually copy persisted workflow metadata into
generated workflow client kwargs.

#### Scenario: Workflow create accepts an extraction definition

- **GIVEN** an `ExtractionDefinition`
- **WHEN** a caller invokes
  `GroundX.create_extraction_workflow(definition=..., name=...)`
- **THEN** the SDK sends `extract` from the definition
- **AND** copies workflow-level `template`, `custom_steps`, `output_routes`,
  and `leaf_fields` into generated workflow create kwargs when present
- **AND** returns the generated `WorkflowResponse`
- **AND** workflow assignment to a bucket or account remains an explicit
  follow-up call such as `client.workflows.add_to_id(...)` or
  `client.workflows.add_to_account(...)`

#### Scenario: Workflow create accepts a YAML shortcut

- **GIVEN** a local extraction YAML file
- **WHEN** a caller invokes `GroundX.create_extraction_workflow(path=..., name=...)`
- **THEN** the SDK internally loads an `ExtractionDefinition` from the YAML
- **AND** performs the same create behavior as the definition-based path

#### Scenario: Workflow create YAML shortcut preserves invalid YAML context

- **GIVEN** a local extraction YAML file with unsupported top-level metadata or
  another structural authoring error
- **WHEN** a caller invokes `GroundX.create_extraction_workflow(path=..., name=...)`
- **THEN** the SDK fails before calling the workflow API
- **AND** the error includes the YAML path or source context
- **AND** the error preserves the actionable loader message naming the offending
  key or malformed path

#### Scenario: Workflow create YAML shortcut accepts supported policy metadata

- **GIVEN** a local extraction YAML file with top-level
  `extraction_policy_version: v1`
- **WHEN** a caller invokes `GroundX.create_extraction_workflow(path=..., name=...)`
- **THEN** the SDK loads the YAML without caller-specific metadata registration
- **AND** the workflow API payload preserves the policy marker in `extract`

#### Scenario: Workflow update accepts an extraction definition

- **GIVEN** an existing workflow ID and an `ExtractionDefinition`
- **WHEN** a caller invokes
  `GroundX.update_extraction_workflow(id, definition=..., name=...)`
- **THEN** the SDK sends a full workflow settings overlay to generated
  `workflows.update(...)`
- **AND** does not teach or perform name-only metadata updates for extraction
  workflows
- **AND** returns the generated `WorkflowResponse`

#### Scenario: Workflow update accepts a YAML shortcut

- **GIVEN** an existing workflow ID and a local extraction YAML file
- **WHEN** a caller invokes
  `GroundX.update_extraction_workflow(id, path=..., name=...)`
- **THEN** the SDK internally loads an `ExtractionDefinition` from the YAML
- **AND** performs the same update behavior as the definition-based path

#### Scenario: Workflow update YAML shortcut preserves invalid YAML context

- **GIVEN** an existing workflow ID and a local extraction YAML file with
  unsupported top-level metadata or another structural authoring error
- **WHEN** a caller invokes
  `GroundX.update_extraction_workflow(id, path=..., name=...)`
- **THEN** the SDK fails before calling the workflow API
- **AND** the error includes the YAML path or source context
- **AND** the error preserves the actionable loader message naming the offending
  key or malformed path

#### Scenario: Workflow update YAML shortcut accepts supported policy metadata

- **GIVEN** an existing workflow ID and a local extraction YAML file with
  top-level `extraction_policy_version: v1`
- **WHEN** a caller invokes
  `GroundX.update_extraction_workflow(id, path=..., name=...)`
- **THEN** the SDK loads the YAML without caller-specific metadata registration
- **AND** the workflow API payload preserves the policy marker in `extract`

#### Scenario: Create/update source selection applies definition precedence

- **GIVEN** a caller wants to create or update an extraction workflow
- **WHEN** they provide source input
- **THEN** `definition` takes precedence over `path`, `yaml_text`, `mapping`,
  and `prepared`
- **AND** if `definition` is absent, exactly one YAML/prepared source is
  required
- **AND** if `definition` is absent, passing zero or multiple YAML/prepared
  sources fails clearly
- **AND** `mapping_kind` is valid only when `mapping` is the selected
  YAML/prepared source
- **AND** generated workflow kwargs assembly remains internal SDK plumbing, not
  the promoted public technique

#### Scenario: Prepared extraction YAML remains the advanced surface

- **GIVEN** a caller needs final groups, workflow groups, pseudo groups, route
  maps, or separated metadata
- **WHEN** they call `prepare_extraction_yaml(...)`
- **THEN** the SDK still returns `PreparedExtractionYaml`
- **AND** the first-class methods do not remove, rename, or repurpose that
  lower-level API
- **AND** callers may load an `ExtractionDefinition` from an existing
  `PreparedExtractionYaml`
- **AND** callers must tolerate `definition.prepared is None` when the
  definition was loaded from a workflow that lacks authored metadata

#### Scenario: Custom workflow steps do not accidentally run fixed defaults

- **GIVEN** an extraction definition with `workflow.custom_steps`
- **WHEN** workflow create/update kwargs are produced and no explicit `steps`
  override is provided
- **THEN** the SDK includes an empty fixed-step overlay equivalent to the
  harness custom-workflow path for exactly these seven stage attributes:
  `chunk_instruct`, `chunk_keys`, `chunk_summary`, `doc_keys`, `doc_summary`,
  `sect_instruct`, and `sect_summary`
- **AND** the generated workflow request serializes the corresponding disabled
  wire keys: `chunk-instruct`, `chunk-keys`, `chunk-summary`, `doc-keys`,
  `doc-summary`, `sect-instruct`, and `sect-summary`
- **AND** the SDK does not add `search_query` or `sect_keys` to that default
  overlay in this plan
- **AND** authored custom steps are not run alongside omitted fixed-step
  defaults
- **AND** legacy YAML without custom workflow steps preserves the old default
  behavior unless the caller supplies explicit `steps`

#### Scenario: Async workflow create/update has parity

- **GIVEN** an async GroundX client
- **WHEN** a caller invokes `AsyncGroundX.create_extraction_workflow(...)` or
  `AsyncGroundX.update_extraction_workflow(...)`
- **THEN** the methods accept the same definition and source arguments as the
  sync client
- **AND** they await the generated async workflow create/update calls
- **AND** they return the generated async `WorkflowResponse`

#### Scenario: Async workflow create YAML shortcut preserves invalid YAML context

- **GIVEN** a local extraction YAML file with unsupported top-level metadata or
  another structural authoring error
- **WHEN** a caller invokes
  `AsyncGroundX.create_extraction_workflow(path=..., name=...)`
- **THEN** the SDK fails before calling the workflow API
- **AND** the error includes the YAML path or source context
- **AND** the error preserves the actionable loader message naming the offending
  key or malformed path

#### Scenario: Async workflow create YAML shortcut accepts supported policy metadata

- **GIVEN** a local extraction YAML file with top-level
  `extraction_policy_version: v1`
- **WHEN** a caller invokes
  `AsyncGroundX.create_extraction_workflow(path=..., name=...)`
- **THEN** the SDK loads the YAML without caller-specific metadata registration
- **AND** the workflow API payload preserves the policy marker in `extract`

#### Scenario: Async workflow update YAML shortcut preserves invalid YAML context

- **GIVEN** an existing workflow ID and a local extraction YAML file with
  unsupported top-level metadata or another structural authoring error
- **WHEN** a caller invokes
  `AsyncGroundX.update_extraction_workflow(id, path=..., name=...)`
- **THEN** the SDK fails before calling the workflow API
- **AND** the error includes the YAML path or source context
- **AND** the error preserves the actionable loader message naming the offending
  key or malformed path

#### Scenario: Async workflow update YAML shortcut accepts supported policy metadata

- **GIVEN** an existing workflow ID and a local extraction YAML file with
  top-level `extraction_policy_version: v1`
- **WHEN** a caller invokes
  `AsyncGroundX.update_extraction_workflow(id, path=..., name=...)`
- **THEN** the SDK loads the YAML without caller-specific metadata registration
- **AND** the workflow API payload preserves the policy marker in `extract`

### Requirement: Docs and harnesses prefer path-first create/update

Public documentation and harness templates SHALL teach first-class workflow
helpers as the primary SDK path once the SDK implementation exists. The common
create/update flow passes a YAML path directly to create/update. Definition
loading is promoted for inspection, reuse, and copying settings from an existing
workflow while preserving fallback paths for older SDKs and offline workflow
JSON compilation.

#### Scenario: Methods are documented as hand-written SDK helpers

- **GIVEN** the Python SDK ships hand-written helpers such as `ingest` and
  `ingest_directories`
- **WHEN** extraction definition and workflow helpers are added
- **THEN** `load_extraction_definition`,
  `load_extraction_definition_from_yaml`,
  `load_extraction_definition_from_workflow`, `create_extraction_workflow`, and
  `update_extraction_workflow` are documented with comparable method-level
  coverage
- **AND** SDK docstrings include parameters, return values, examples, and update
  semantics
- **AND** public docs and harness references list them as hand-written Python
  SDK helpers rather than generated Fern endpoints
- **AND** architecture or API-surface references that enumerate hand-written SDK
  helpers are updated
- **AND** SDK docs make the `groundx[extract]` dependency boundary explicit
- **AND** harness public extraction-doc guidance is updated so
  `prepare_extraction_yaml(...)` is not the primary public create/update path

#### Scenario: Public docs replace manual metadata copying

- **GIVEN** public extraction workflow docs
- **WHEN** they show how to create or update a workflow from YAML
- **THEN** the primary example uses
  `client.create_extraction_workflow(path=..., name=...)`
- **AND** update examples use
  `client.update_extraction_workflow(id, path=..., name=...)`
- **AND** definition examples use `client.load_extraction_definition(...)` only
  when the caller needs to inspect, reuse, or copy workflow settings
- **AND** create examples keep the explicit workflow ID extraction and
  bucket/account assignment step
- **AND** manual extraction of `persisted_workflow_extract["workflow"]` and
  manual copying of `template`, `custom_steps`, `output_routes`, and
  `leaf_fields` is not the primary path

#### Scenario: Harness keeps fallback until SDK minimum moves

- **GIVEN** harness templates that may run with older SDK versions
- **WHEN** the installed client has extraction definition and workflow helpers
- **THEN** deploy/run/batch/prompt-manager paths use the helper methods
- **AND** when the helpers are absent, the templates fall back to existing
  `build_workflow_artifacts(...)` and `workflow_sdk_kwargs(...)`
- **AND** offline compile output remains available
- **AND** helper-backed deploy paths still write and validate the same
  reproducible `workflow.json` and `extraction_workflow_metadata_v1.json`
  artifacts before making API calls
- **AND** source-of-truth surfaces such as `SKILL.md`, reference docs, evals,
  scanners, routing/source manifests, generated plugin mirrors, and version or
  changelog files are updated when their contracts are touched

#### Scenario: Public docs and harness helper preference wait for released SDK

- **GIVEN** the SDK helper implementation has not yet been published and
  verified from a fresh `groundx[extract]` install
- **WHEN** public docs or harness helper-preference PRs are prepared
- **THEN** those PRs remain draft-only or blocked from merge
- **AND** public docs do not claim the helpers are available until the release
  gate is complete
- **AND** harness templates keep the older-SDK fallback covered when the
  minimum supported SDK version has not been bumped

#### Scenario: Web UI guidance preserves authenticated base experience

- **GIVEN** this plan touches GroundX Studio Harness web UI, publish, scaffold,
  or onboarding references
- **WHEN** those docs or tests are updated
- **THEN** they continue to describe the base product experience as an
  authenticated app shell
- **AND** onboarding remains a configurable overlay/app metadata flow for
  first-session guidance
- **AND** no docs or templates introduce an anonymous onboarding-first base app
  unless a separate approved web UI plan explicitly changes that behavior

#### Scenario: Arcadia adoption is equivalence-gated

- **GIVEN** Arcadia prompt management uses specialized extraction metadata keys
- **WHEN** helper adoption is considered
- **THEN** tests compare first-class-method behavior with the existing explicit
  Arcadia workflow kwargs
- **AND** equivalence includes `extract`, `_groundx_persisted_extract`,
  serialized `steps`, `chunk_strategy`, `section_strategy`, workflow `name`, and
  update `id`
- **AND** Arcadia adopts the methods only if behavior is equivalent
- **AND** otherwise Arcadia records a no-op decision and keeps its lower-level
  explicit path

### Requirement: Convenience helpers do not change Fern schema names

This change SHALL NOT rename generated OpenAPI/Fern schemas or generated SDK
classes.

#### Scenario: Generated schema imports remain stable

- **GIVEN** generated types such as `CustomWorkflowStepConfig`
- **WHEN** this convenience-method change is implemented
- **THEN** those generated schema names remain unchanged
- **AND** normal extraction workflow callers no longer need to import them for
  YAML-based workflow load/create/update
- **AND** any future schema-name cleanup is handled by a separate approved plan

### Requirement: Extraction workflow create/update validates supported shapes

The SDK first-class extraction workflow helpers SHALL validate input definition
shape before calling the workflow API.

#### Scenario: Create accepts pure legacy

- **GIVEN** a caller creates an extraction workflow from pure legacy YAML
- **WHEN** `create_extraction_workflow(...)` validates the source
- **THEN** the helper accepts the definition
- **AND** it sends a legacy-compatible workflow `extract` payload.

#### Scenario: Create accepts explicit v1

- **GIVEN** a caller creates an extraction workflow from YAML containing
  `extraction_policy_version: v1`
- **WHEN** `create_extraction_workflow(...)` validates the source
- **THEN** the helper accepts the definition
- **AND** it preserves v1 persisted metadata in the workflow `extract` payload.

#### Scenario: Create rejects mixed metadata

- **GIVEN** a caller creates an extraction workflow from metadata-bearing YAML
  that lacks `extraction_policy_version: v1`
- **WHEN** `create_extraction_workflow(...)` validates the source
- **THEN** the helper fails before calling the workflow API
- **AND** the error identifies the source as mixed or unsupported.

#### Scenario: Legacy update without existing state is not rejected by downgrade guard

- **GIVEN** a caller updates an extraction workflow with pure legacy YAML
- **AND** the SDK helper does not have existing-workflow state
- **WHEN** `update_extraction_workflow(...)` validates the update
- **THEN** the helper does not reject the update solely because the existing
  workflow shape is unknown
- **AND** it does not perform a hidden `workflows.get(...)` preflight read solely
  to enforce downgrade safety
- **AND** server-side workflow validation remains responsible for rejecting an
  accidental v1-to-legacy downgrade when stored workflow state is available.

#### Scenario: SDK does not add client-side downgrade option in this phase

- **GIVEN** a caller updates an extraction workflow through the SDK helper
- **WHEN** the helper validates the supplied extraction definition
- **THEN** the helper does not require or expose an `allow_legacy_downgrade`
  option in this change
- **AND** it does not infer existing workflow shape from `workflow_id`
- **AND** any future client-side downgrade guard requires a separately specified
  explicit existing-workflow context surface.

### Requirement: Extraction error callback bodies preserve required identity

SDK extraction task error helpers SHALL be able to build a callback-compatible
error body from fatal task identifiers even when a full typed request object is
unavailable.

#### Scenario: Minimal fatal callback body is valid

- **GIVEN** a fatal extraction task error has a callback URL, document ID, task
  ID, code, and message
- **WHEN** the SDK error helper builds the callback body
- **THEN** the body contains `documentID`, `taskID`, `code`, and `message`
- **AND** the body is accepted by the GroundX extraction callback handler.

#### Scenario: Optional processor identity is preserved

- **GIVEN** a fatal extraction task error also has model ID or processor ID
- **WHEN** the SDK error helper builds the callback body
- **THEN** those identifiers are included when supported by the callback
  contract
- **AND** callers that only have the minimal required identifiers remain
  supported.
