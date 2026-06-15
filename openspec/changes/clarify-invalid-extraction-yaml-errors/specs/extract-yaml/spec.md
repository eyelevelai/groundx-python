## MODIFIED Requirements

### Requirement: Prepared extraction YAML accepts persisted workflow extract mappings
The SDK SHALL support preparing extraction definitions from either raw YAML text
or a workflow API `extract` mapping produced by the persisted workflow extract
surface.

#### Scenario: Unsupported top-level scalar metadata fails clearly
- **WHEN** raw authored YAML contains a top-level scalar key that is not a
  reserved SDK key, not supported SDK metadata, and was not registered through
  `top_level_metadata_keys`
- **THEN** `prepare_extraction_yaml(...)` raises a `ValueError` naming the
  offending key
- **AND** the error explains that generic SDK top-level keys must be extraction
  groups, reserved SDK keys, or supported SDK metadata keys
- **AND** the error tells advanced callers to register metadata keys through
  `top_level_metadata_keys` or convert the YAML to supported workflow metadata

#### Scenario: Supported policy version metadata is preserved
- **WHEN** raw authored YAML contains top-level
  `extraction_policy_version: v1`
- **THEN** `prepare_extraction_yaml(...)` succeeds without caller-specific
  metadata registration
- **AND** the marker is exposed in `PreparedExtractionYaml.top_level_metadata`
- **AND** the marker is preserved in the persisted workflow extract

#### Scenario: Explicit metadata registration still works
- **WHEN** the same authored YAML is prepared with the scalar key included in
  `top_level_metadata_keys`
- **THEN** preparation succeeds
- **AND** the key is exposed as top-level metadata rather than as an extraction
  group
