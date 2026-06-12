## ADDED Requirements

### Requirement: SDK readback exposes custom output maps

The SDK SHALL parse and expose custom chunk, section, and document output maps
from X-Ray/readback responses while preserving legacy fixed readback fields.

#### Scenario: Custom output maps load from X-Ray

- **GIVEN** an X-Ray/readback response with `customChunkOutputs`,
  `customSectionOutputs`, and `customDocumentOutputs`
- **WHEN** the SDK loads the response into extract classes
- **THEN** chunk-level custom values are readable from `customChunkOutputs`
- **AND** section-level custom values are readable from `customSectionOutputs`
- **AND** document-level custom values are readable from
  `customDocumentOutputs`
- **AND** matching page-level chunk paths are parsed when X-Ray includes
  `documentPages[].chunks[]`

#### Scenario: Fixed readback fields remain stable

- **GIVEN** an old X-Ray/readback response that contains fixed outputs only
- **WHEN** the SDK loads the response
- **THEN** `chunkKeywords`, `sectionSummary`, and `fileSummary` remain readable
- **AND** missing custom output maps are treated as absent or empty
- **AND** old documents do not require a backfill migration before SDK readback

#### Scenario: Document custom output is not fileSummary

- **GIVEN** a custom document-level output
- **WHEN** the SDK loads X-Ray/readback data
- **THEN** the value is read from top-level `customDocumentOutputs`
- **AND** it is not read from legacy top-level or per-chunk `fileSummary`

