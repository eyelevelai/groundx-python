## ADDED Requirements

### Requirement: Generated workflow clients expose custom workflow config

The generated Python SDK workflow request and response models SHALL represent
the public Fern/OpenAPI custom workflow-step contract after the approved
generation path.

#### Scenario: Workflow request serializes custom config

- **GIVEN** SDK code builds a workflow create or update request
- **WHEN** the request includes workflow-level `template`, `customSteps`,
  `outputRoutes`, `leafFields`, and `requiredTemplateKeys`
- **THEN** the generated request model serializes those fields with the public
  JSON names
- **AND** legacy fixed `steps` fields remain serializable
- **AND** custom step `config` can carry existing element-targeted prompt,
  engine, and include settings while omitting or nulling legacy fixed-output
  `field`

#### Scenario: Workflow detail deserializes custom metadata

- **GIVEN** the workflow API returns persisted custom workflow-step metadata
- **WHEN** the generated SDK deserializes workflow detail
- **THEN** it exposes `customSteps`, `outputRoutes`, `leafFields`, `template`,
  field-count metadata, and custom output map schemas without dropping fields
- **AND** fixed workflow details still deserialize with existing fields

#### Scenario: Generated files come from the approved source path

- **GIVEN** generated SDK files change for custom workflow steps
- **WHEN** the SDK change is reviewed
- **THEN** the generated files came from the upstream Fern/OpenAPI source and
  approved generation or release path
- **AND** handwritten extract implementation did not directly edit generated
  files outside that path
