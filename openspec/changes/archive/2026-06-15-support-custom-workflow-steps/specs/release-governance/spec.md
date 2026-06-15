## ADDED Requirements

### Requirement: Downstream docs and repos follow publish-last e2e releases

Public SDK and docs publishing SHALL happen late in the sequence, after local
runtime, schema, SDK, and harness verification, because the final end-to-end
test is expected to require published SDK and docs artifacts. Downstream repos
SHALL move only after that published-artifact e2e path passes.

#### Scenario: Public docs describe implemented behavior

- **GIVEN** public docs that explain custom workflow steps
- **WHEN** those docs are published for final end-to-end validation
- **THEN** local Go runtime, Python SDK, and harness compile/readback
  verification has already passed
- **AND** the docs do not describe harness-only behavior as public API behavior
- **AND** the published docs are included in the final e2e proof path

#### Scenario: Downstream repos use a lower-bound SDK dependency

- **GIVEN** a downstream repo needs the released SDK feature
- **WHEN** the published SDK/docs/runtime e2e path has passed
- **AND** its dependency is updated
- **THEN** the dependency uses a lower bound such as
  `groundx-python >= <released version>`
- **AND** it does not pin exactly to one SDK version unless explicitly approved

#### Scenario: Fern schema change accounts for TypeScript generation

- **GIVEN** the shared Fern OpenAPI schema changes for custom steps or
  `template`
- **WHEN** release readiness is reviewed
- **THEN** TypeScript generation has a passing smoke check using
  `fern generate --group ts-sdk`
- **AND** the smoke evidence shows the generator accepts `customSteps`,
  custom step `config`, custom step legacy `field` rejection, `outputRoutes`,
  `outputKey`, `leafFields`, route/leaf matching fields, `isRepeated`,
  `repetitionScope`, wildcard repeated-item final paths, `template`,
  `requiredTemplateKeys`, reserved template key validation, the custom output map
  schemas, and the 20-field validation/metadata schema without generator errors
- **AND** Python SDK behavior remains the release blocker for this feature
- **AND** TypeScript feature documentation and examples may be deferred only if
  generation compatibility is still proven

#### Scenario: Generated SDK and docs publish as the final e2e prerequisite

- **GIVEN** the Fern/OpenAPI contract has been updated for custom workflow steps
  or `template`
- **WHEN** generated SDKs or public docs must be published for final end-to-end
  testing
- **THEN** `cashbot-go`, Python SDK, harness compile/readback, TypeScript
  generation smoke, and mirrored OpenAPI surfaces have already passed local or
  repo-level verification
- **AND** publishing is treated as the final prerequisite before the e2e run
- **AND** downstream dependency changes wait until the published-artifact e2e
  run passes

#### Scenario: Local generation verifies the contract before publish

- **GIVEN** the Fern/OpenAPI branch defines custom workflow steps or `template`
- **WHEN** SDK and runtime work need generated surfaces for tests
- **THEN** local Python and TypeScript generation or generator smoke output may
  be used before publishing a released SDK
- **AND** those local generated artifacts do not count as a public SDK release
- **AND** public SDK and docs publishing wait until runtime, SDK, harness, and
  mirrored OpenAPI verification pass
- **AND** downstream dependency bumps wait until the published-artifact e2e path
  passes

#### Scenario: Published-artifact e2e can fail after publish

- **GIVEN** the SDK and docs have been published as the final e2e prerequisite
- **WHEN** the end-to-end test against the published artifacts fails
- **THEN** the release is recorded as failed
- **AND** follow-up work fixes forward with a corrective patch or replacement
  publication
- **AND** downstream dependency bumps and customer-facing closeout remain blocked
  until the corrected published-artifact e2e path passes

#### Scenario: Generated SDK files come from the approved source path

- **GIVEN** generated Python SDK files change for custom workflow steps or
  `template`
- **WHEN** the SDK repo is reviewed for release readiness
- **THEN** the generated files came from the upstream Fern/OpenAPI source and the
  approved regeneration or release path
- **AND** hand-written implementation commits did not directly edit generated
  files outside that path
- **AND** local generated artifacts used for verification are identified as
  non-release artifacts unless the approved release workflow produced the commit

#### Scenario: Release closeout requires deployed-path proof or an approved substitute

- **GIVEN** downstream dependency bumps or customer-facing release closeout are
  considered
- **WHEN** live credentials, documents, or deployment approval are unavailable
- **THEN** release remains blocked unless an explicitly reviewed non-live
  substitute proves workflow create/update, persisted extract metadata, X-Ray or
  readback shape, route metadata, and final JSON reassembly
- **AND** skipped live checks are recorded with the approving reviewer and the
  substitute evidence
