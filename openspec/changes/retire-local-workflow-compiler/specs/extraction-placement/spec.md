# Spec delta: extraction-placement

## MODIFIED Requirements

### Requirement: GroundX Python owns reassembly from canonical metadata

GroundX Python SHALL reassemble X-Ray and custom output from canonical route
and relationship metadata supplied by the server. It SHALL NOT compile authored
workflow YAML or reconstruct missing compiler-owned metadata.

#### Scenario: reassembly consumes supplied placement

- **GIVEN** X-Ray custom output and valid server-compiled route metadata
- **WHEN** GroundX Python reassembles the custom output
- **THEN** it writes values to the supplied destinations
- **AND** it does not recalculate placement from group names, roles, prompts,
  aliases, field policy, values, or path depth.

#### Scenario: relationship selection consumes supplied metadata

- **GIVEN** canonical relationship metadata and ordered parent candidates
- **WHEN** GroundX Python selects a relationship parent
- **THEN** it applies the stable-first populated-key algorithm
- **AND** it does not derive relationship metadata from authored YAML.
