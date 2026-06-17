## ADDED Requirements

### Requirement: Chunk model exposes per-step custom chunk and section outputs
The `Chunk` Pydantic model SHALL add two new optional fields:
- `customChunkOutputs: Optional[Dict[str, Any]] = None`
- `customSectionOutputs: Optional[Dict[str, Any]] = None`

The model's `model_config` SHALL include `extra="allow"` so that additional unknown
X-Ray fields do not cause validation errors (tolerant reader).
When the X-Ray JSON contains `customChunkOutputs` or `customSectionOutputs` on a chunk
entry the values SHALL be parsed and accessible on the `Chunk` instance.

#### Scenario: Custom chunk outputs are parsed from X-Ray JSON
- **WHEN** an X-Ray JSON chunk entry contains
  `"customChunkOutputs": {"adp_chunk_01": {"plan_type": "401k"}}`
- **THEN** `Chunk(**chunk_dict).customChunkOutputs` equals
  `{"adp_chunk_01": {"plan_type": "401k"}}`
- **AND** all other existing `Chunk` fields retain their original values

#### Scenario: Custom section outputs are parsed from X-Ray JSON
- **WHEN** an X-Ray JSON chunk entry contains
  `"customSectionOutputs": {"adp_section_01": {"section_name": "Contributions"}}`
- **THEN** `Chunk(**chunk_dict).customSectionOutputs` equals
  `{"adp_section_01": {"section_name": "Contributions"}}`

#### Scenario: Chunk without custom outputs remains unchanged
- **WHEN** an X-Ray JSON chunk entry contains no `customChunkOutputs` or
  `customSectionOutputs` keys
- **THEN** the constructed `Chunk` has `customChunkOutputs` as `None` and
  `customSectionOutputs` as `None`
- **AND** all existing `Chunk` field-parsing behavior is unchanged

#### Scenario: Unknown additional X-Ray fields do not raise ValidationError
- **WHEN** an X-Ray JSON chunk entry contains a field not declared on `Chunk`
  (e.g. `"futureField": "value"`)
- **THEN** constructing the `Chunk` does NOT raise `ValidationError`
- **AND** the unknown field is accessible via the Pydantic extra-fields mechanism

### Requirement: XRayDocument model exposes per-step custom document outputs
The `XRayDocument` Pydantic model SHALL add one new optional field:
- `customDocumentOutputs: Optional[Dict[str, Any]] = None`

The model's `model_config` SHALL include `extra="allow"`.
When the X-Ray JSON contains `customDocumentOutputs` at the document level the value
SHALL be parsed and accessible on the `XRayDocument` instance.

#### Scenario: Custom document outputs are parsed from X-Ray JSON
- **WHEN** an X-Ray JSON document payload contains
  `"customDocumentOutputs": {"adp_doc_01": {"plan_name": "ADP 401k"}}`
- **THEN** `XRayDocument(**payload).customDocumentOutputs` equals
  `{"adp_doc_01": {"plan_name": "ADP 401k"}}`
- **AND** `XRayDocument.chunks` and all existing document-level fields are unchanged

#### Scenario: XRayDocument without custom outputs remains unchanged
- **WHEN** an X-Ray JSON document payload contains no `customDocumentOutputs` key
- **THEN** the constructed `XRayDocument` has `customDocumentOutputs` as `None`
- **AND** all existing `XRayDocument` field-parsing behavior is unchanged

#### Scenario: Unknown additional document-level X-Ray fields do not raise ValidationError
- **WHEN** an X-Ray JSON document payload contains a field not declared on
  `XRayDocument` (e.g. `"newTopLevelField": "value"`)
- **THEN** constructing the `XRayDocument` does NOT raise `ValidationError`

### Requirement: XRayDocument.download returns a model that includes custom outputs
`XRayDocument.download` SHALL return an `XRayDocument` instance that exposes custom
output fields when the fetched X-Ray JSON — whether from cache, object-store, or HTTP —
contains `customDocumentOutputs`, `customChunkOutputs`, or `customSectionOutputs`.

#### Scenario: Custom chunk outputs accessible after download
- **WHEN** `XRayDocument.download` loads an X-Ray JSON whose first chunk contains
  `"customChunkOutputs": {"my_step": {"result": 1}}`
- **THEN** the returned `XRayDocument.chunks[0].customChunkOutputs` equals
  `{"my_step": {"result": 1}}`

### Requirement: Backward-compatibility — X-Ray parsing unchanged for documents without custom outputs
Adding optional custom-output fields to `Chunk` and `XRayDocument` SHALL NOT change
the behavior of any existing X-Ray parsing path.

#### Scenario: Existing X-Ray JSON (no custom outputs) parses identically to before
- **WHEN** an X-Ray JSON payload was produced by a workflow that uses only fixed slots
  (no custom steps)
- **THEN** `XRayDocument(**payload)` succeeds and all chunk fields (`chunk`, `chunkKeywords`,
  `sectionSummary`, etc.) have the same values as they did before this change
- **AND** `customChunkOutputs`, `customSectionOutputs`, and `customDocumentOutputs` are
  all `None` on each object
