# Spec delta: extract-yaml

## ADDED Requirements

### Requirement: canonical workflow processing roles are authored

For a canonical v1 workflow with an `agent_chain`, the SDK SHALL require every
final group and pseudo group to declare an explicit processing `role`. It SHALL
use that role for branch validation and serial task coverage. It SHALL NOT infer
role from group name, task suffix, field vocabulary, or shape.

#### Scenario: renaming a group does not change validation

- **GIVEN** two otherwise identical canonical workflows whose group names differ
- **AND** their authored roles and agent chains are identical
- **WHEN** the SDK validates them
- **THEN** both produce the same result.

#### Scenario: a missing role fails independently of name

- **GIVEN** a canonical workflow group used by an agent chain has no role
- **WHEN** the SDK validates the workflow
- **THEN** validation fails whether the group name is `charges`, `fees`, or any
  other value.

#### Scenario: a parallel branch must match its authored role

- **GIVEN** a parallel branch invokes meter tasks for a group authored with the
  `charges` role
- **WHEN** the SDK validates the workflow
- **THEN** validation fails with the role mismatch.

#### Scenario: persisted reload preserves roles

- **GIVEN** a canonical authored workflow with explicit roles is prepared
- **WHEN** its persisted workflow mapping is loaded again
- **THEN** every authored role is preserved
- **AND** agent-chain validation produces the same result.
