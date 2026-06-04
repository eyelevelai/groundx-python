## ADDED Requirements

### Requirement: Extract YAML parser edge cases are regression tested

The SDK extraction YAML parser SHALL have named regression tests for supported
and rejected pseudo-group authoring edge cases that are not already covered by
the core prompt manager test suite.

#### Scenario: Duplicate fixture candidates are audited before implementation

- **GIVEN** a proposed parser-hardening fixture
- **WHEN** existing `tests/extract/prompt/test_manager.py` coverage already
  proves the same behavior
- **THEN** the duplicate hardening task is removed or marked covered
- **AND** no redundant test is added only to satisfy a checklist

#### Scenario: New parser behavior gaps are fixed intentionally

- **GIVEN** a new hardening fixture exposes behavior that differs from the
  released YAML contract
- **WHEN** the fixture fails
- **THEN** the SDK implementation is fixed in a focused patch
- **AND** the change is reviewed for compatibility with legacy YAML and
  released pseudo-group semantics
