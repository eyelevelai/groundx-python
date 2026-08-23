# Proposal: require authored workflow group roles

## Why

Agent-chain validation inferred processing roles from task suffixes and group
names. Identical groups could therefore validate differently after a rename.

## What changes

- Require every canonical v1 final and pseudo group used by an agent chain to
  declare its processing `role`.
- Validate each parallel branch against the authored role.
- Resolve serial task coverage by authored role, never group name.
- Preserve roles across persisted-workflow reload.

Pure Arcadia legacy role synthesis remains Cashbot-owned. This SDK change is a
pre-implemented slice of Cashbot's
`complete-canonical-workflow-compiler-migration` task 11.3 and does not create
another compiler or fixture path.
