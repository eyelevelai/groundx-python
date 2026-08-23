# extraction-placement Specification

## Purpose

Define GroundX Python's ownership of extraction YAML parser/compiler parity and
X-Ray/custom-output reassembly, including the boundary between processing role
and authored final JSON placement.

## Requirements

### Requirement: GroundX Python owns SDK placement parity and reassembly

GroundX Python SHALL own its hand-written extraction YAML parser/compiler
behavior and keep the resulting route metadata in parity with the canonical
production compiler. GroundX Python SHALL also own production
X-Ray/custom-output reassembly from compiled route metadata.

This ownership does not make the SDK the product YAML upload compiler. It makes
the SDK responsible for accepting the supported authored contract, producing
equivalent routes when it compiles locally, and preserving canonical routes
when it reassembles custom output.

#### Scenario: Equivalent authored YAML produces equivalent routes

- **GIVEN** supported v1 authored YAML is compiled by GroundX Python and by the
  canonical production compiler
- **WHEN** their normalized output routes and leaf fields are compared
- **THEN** both compilers describe the same final destinations
- **AND** the SDK does not introduce a second placement policy.

#### Scenario: Reassembly consumes compiled placement

- **GIVEN** X-Ray custom output and valid compiled route metadata
- **WHEN** GroundX Python reassembles the custom output
- **THEN** it writes values to the compiled destinations
- **AND** it does not recalculate placement from group names, processing role,
  field policy, aliases, or extracted values.

### Requirement: Processing role and authored placement are independent

`role` SHALL select processing and relationship direction. `output_scope` SHALL
select authored placement for a direct v1 group. A direct group without an
explicit document-root scope remains under its authored group. Only a
non-repeating direct group may declare `output_scope: document_root`.

#### Scenario: The same role supports different placements

- **GIVEN** two direct v1 groups use the same processing `role`
- **AND** only one declares `output_scope: document_root`
- **WHEN** their routes are compiled
- **THEN** both use the same processing behavior
- **AND** the document-root group routes beneath `/`
- **AND** the other group routes beneath its authored group.

#### Scenario: Repeating groups stay grouped

- **GIVEN** a repeating direct group declares document-root scope
- **WHEN** GroundX Python prepares the authored YAML
- **THEN** preparation fails with a clear placement error.

### Requirement: Final paths are complete destination trees

Each `final_path` SHALL be the complete destination tree, including every
nested segment and each `*` segment that identifies a repeated object. GroundX
Python SHALL preserve that tree through preparation and X-Ray/custom-output
reassembly. Path depth SHALL never determine output scope.

#### Scenario: Root and grouped paths can both be nested

- **GIVEN** compiled routes include a root scalar `/field`, a root nested field
  `/object/field`, and a grouped nested field `/group/object/field`
- **WHEN** GroundX Python reassembles custom output
- **THEN** each value is written to its complete compiled destination
- **AND** segment count is not used to infer whether the destination is root or
  grouped.

#### Scenario: Repeated paths retain their repeated position

- **GIVEN** a compiled route includes a repeated destination such as
  `/group/*/object/field`
- **WHEN** GroundX Python prepares and reassembles the route
- **THEN** the `*` remains at the compiled repeated-object position
- **AND** the SDK does not shorten the path or invent an enclosing group.
