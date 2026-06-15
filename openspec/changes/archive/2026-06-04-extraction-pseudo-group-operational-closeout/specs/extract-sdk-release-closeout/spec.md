## ADDED Requirements

### Requirement: Extract SDK release readiness is evidence gated

Pseudo-group extraction closeout SHALL treat the Python SDK package as ready
for downstream harness and documentation only after a published package can be
installed in a clean environment and the public extraction preparation imports
resolve without development-only dependencies.

#### Scenario: Published package passes clean extraction import

- **GIVEN** a freshly created virtual environment
- **WHEN** the released package `groundx[extract]==3.6.0` is installed
- **THEN** `from groundx.extract import FinalFieldPath, PreparedExtractionYaml, prepare_extraction_yaml` succeeds
- **AND** downstream harness and documentation plans may clear SDK package availability blockers

#### Scenario: Cross-repo work remains open after SDK package readiness

- **GIVEN** the published SDK package import gate has passed
- **WHEN** Arcadia runtime wiring, Fern publish access, or harness fixture hardening remains incomplete
- **THEN** those repo-specific plans remain open
- **AND** the operational closeout plan is not archived until those non-SDK gates are either complete or explicitly moved to successor work
