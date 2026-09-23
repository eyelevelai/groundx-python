## ADDED Requirements

### Requirement: Singular prompt lookups copy only requested values

After normal workflow cache/version resolution, `PromptManager.group_field(group_name, attr_name)`, `group_load(group_name)`, and `get_prompt(name)` SHALL return defensive copies of only their selected field, group, or prompt. They SHALL preserve the existing return types, `None` result for a missing field, and errors for invalid or missing paths. A caller's mutation SHALL not affect the cached definition or another lookup.

#### Scenario: Repeated field lookup in a large workflow

- **GIVEN** a cached workflow with several groups
- **WHEN** a caller repeatedly requests one field
- **THEN** each result is independent and no unrelated group is copied

#### Scenario: Nested group and prompt lookup

- **GIVEN** a cached nested group
- **WHEN** a caller loads the nested group or one nested prompt
- **THEN** only the selected object is copied and path validation remains unchanged

#### Scenario: Missing field and missing path

- **GIVEN** a cached workflow without the requested entry
- **WHEN** a caller requests a missing field or invalid path
- **THEN** the singular accessor retains its existing `None` or exception behavior

### Requirement: Whole-workflow getters remain defensive

`get_fields_for_workflow` and `get_fields_for_data_object` SHALL continue to return independent whole-workflow copies for callers that explicitly request them.

#### Scenario: Caller edits a whole-workflow result

- **WHEN** a caller mutates a returned workflow group
- **THEN** later lookups still return the original cached definition
