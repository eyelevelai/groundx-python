# Proposal: retire the local workflow compiler

## Why

GroundX Python still compiles authored extraction YAML into execution JSON.
Cashbot now owns workflow validation, compilation, canonical metadata, and
schema identity. Keeping both compilers lets identical YAML produce different
behavior.

## What changes

- Send authored YAML unchanged through workflow create and update helpers.
- Remove SDK APIs and types that create or reconstruct compiler-owned metadata.
- Preserve workflow readback, custom-output reassembly, and relationship
  selection from server-supplied metadata.
- Release the removal as an explicit breaking SDK change after consumers move
  to raw-YAML authoring.

This implements the GroundX Python portion of Cashbot's
`complete-canonical-workflow-compiler-migration` tasks 11.3, 11.6, and 11.9.
