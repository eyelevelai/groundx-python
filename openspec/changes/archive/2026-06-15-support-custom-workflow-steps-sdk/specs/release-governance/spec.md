## ADDED Requirements

### Requirement: Python SDK release follows publish-last gates

The Python SDK SHALL be published only after local/runtime/schema/SDK/harness
verification is complete and immediately before any final e2e path that
requires a published SDK artifact.

#### Scenario: Local generated output is verification, not release

- **GIVEN** local generated Python SDK output is used to test custom workflow
  steps before public publication
- **WHEN** verification is reviewed
- **THEN** the local generated output is identified as non-release evidence
- **AND** downstream dependency bumps do not depend on that local output

#### Scenario: Published SDK is final e2e prerequisite

- **GIVEN** Fern/OpenAPI, cashbot-go runtime/API, SDK extract behavior, harness
  compile/readback, and TypeScript generation smoke have passed
- **WHEN** the final e2e path requires a published SDK
- **THEN** publishing the SDK is allowed as the final prerequisite
- **AND** downstream repos use a lower-bound dependency such as
  `groundx-python >= <released version>` only after the published-artifact e2e
  passes

#### Scenario: Published-artifact e2e failure blocks downstream movement

- **GIVEN** the SDK has been published as the final e2e prerequisite
- **WHEN** the published-artifact e2e path fails
- **THEN** the release is recorded as failed
- **AND** downstream dependency bumps and customer-facing closeout remain
  blocked until a corrective publication or approved replacement path passes
