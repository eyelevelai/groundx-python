## ADDED Requirements

### Requirement: Custom outputs are readable after extraction

The runtime and SDK SHALL expose custom chunk, section, and document outputs in
documented X-Ray/readback maps named `customChunkOutputs`,
`customSectionOutputs`, and `customDocumentOutputs`.

The custom output shape SHALL be additive to the existing fixed X-Ray fields.
Existing `chunkKeywords`, `sectionSummary`, `fileSummary`, and related fixed
fields SHALL remain available for legacy workflows and fixed-step consumers.

Custom outputs SHALL be persisted through explicit workflow custom-output
metadata. Chunk-level custom outputs map to molecule-level custom metadata,
section-level custom outputs map to section-level custom metadata, and
document-level custom outputs map to document-level custom metadata. Missing
custom-output metadata on old documents SHALL be treated as empty.

#### Scenario: Custom output readback is predictable

- **GIVEN** a workflow with custom chunk, section, and document steps
- **WHEN** the runtime processes a document and returns X-Ray
- **THEN** custom chunk outputs are available under `customChunkOutputs`
- **AND** custom section outputs are available under `customSectionOutputs`
- **AND** custom document outputs are available under `customDocumentOutputs`
- **AND** the SDK can parse the custom outputs
- **AND** existing fixed outputs such as `chunkKeywords` remain available

#### Scenario: Fixed readback fields remain stable

- **GIVEN** a workflow using only existing fixed step outputs
- **WHEN** the runtime returns X-Ray and the SDK loads the document
- **THEN** chunk keyword output remains available as `chunkKeywords`
- **AND** section summary output remains available as `sectionSummary`
- **AND** document summary output remains available as top-level `fileSummary`
  when the runtime emits one consistent document summary
- **AND** per-chunk document summary output remains available as chunk
  `fileSummary` when the runtime emits divergent chunk-level document summaries
- **AND** custom output support does not require legacy consumers to read a new
  custom output map for those fixed fields

#### Scenario: Custom output route metadata supports reassembly

- **GIVEN** a custom workflow group field routed to a final JSON path
- **WHEN** the runtime returns the field under `customChunkOutputs`,
  `customSectionOutputs`, or `customDocumentOutputs`
- **THEN** workflow metadata identifies the exact custom output path
- **AND** Arcadia can map the custom output value back to the final JSON path
- **AND** custom workflow group names do not appear in the final JSON

#### Scenario: Custom readback paths are exact and level-aware

- **GIVEN** a workflow with custom chunk, section, and document outputs
- **WHEN** route metadata is persisted and read back
- **THEN** each route records the canonical custom step identity
- **AND** each route records the output level: chunk, section, or document
- **AND** each route records the exact X-Ray/readback path used by the SDK and
  Arcadia
- **AND** document-level custom output routes read from `customDocumentOutputs`
  rather than legacy top-level or per-chunk `fileSummary`
- **AND** duplicate custom output destinations fail according to the workflow
  config naming and collision contract

#### Scenario: Route metadata is explicit

- **GIVEN** a custom output routed to a final JSON field
- **WHEN** workflow metadata is persisted
- **THEN** each route records `workflow_group`, `workflow_field`, `final_path`,
  `step_name`, `level`, `output_map`, `output_key`, and `readback_path`
- **AND** `final_path` is an RFC 6901 JSON Pointer to the final JSON field
- **AND** each route has exactly one matching `leaf_fields` record for the same
  `final_path`, `workflow_group`, `workflow_field`, `step_name`, `level`, and
  `output_key`
- **AND** `readback_path` is the X-Ray/readback path template where SDK and
  Arcadia read the value
- **AND** chunk route `readback_path` stores the canonical non-page path
  `/chunks/*/customChunkOutputs/<step_name>/<output_key>`
- **AND** when X-Ray includes page-level chunks, SDK and Arcadia derive the
  companion chunk path
  `/documentPages/*/chunks/*/customChunkOutputs/<step_name>/<output_key>`
- **AND** section route `readback_path` stores the canonical non-page path
  `/chunks/*/customSectionOutputs/<step_name>/<output_key>`
- **AND** when X-Ray includes page-level chunks, SDK and Arcadia derive the
  companion section path
  `/documentPages/*/chunks/*/customSectionOutputs/<step_name>/<output_key>`
- **AND** document readback paths use
  `/customDocumentOutputs/<step_name>/<output_key>`

#### Scenario: Document custom outputs are single document values

- **GIVEN** a document-level custom output
- **WHEN** runtime produces X-Ray
- **THEN** the value is returned through top-level `customDocumentOutputs`
- **AND** the value is not emitted through legacy top-level or per-chunk
  `fileSummary`
- **AND** conflicting per-chunk document custom values fail validation instead
  of producing a divergent document custom output

#### Scenario: Old documents remain readable

- **GIVEN** an old processed document without custom-output metadata
- **WHEN** X-Ray/readback is requested
- **THEN** fixed legacy fields remain readable
- **AND** custom output maps are absent or empty
- **AND** the reader does not require a backfill migration before returning
  legacy X-Ray
