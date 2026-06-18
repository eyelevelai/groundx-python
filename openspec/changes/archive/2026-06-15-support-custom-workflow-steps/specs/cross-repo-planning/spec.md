## ADDED Requirements

### Requirement: Central planning change is not archived as cross-repo truth

The central `groundx-python` OpenSpec change SHALL remain a planning artifact
until repo-owned OpenSpec changes absorb durable behavior requirements.

#### Scenario: Central change is closed without archiving cross-repo specs

- **GIVEN** this central planning change contains draft requirements for
  `cashbot-go`, `eyelevel-fern-config`, `internal-arcadia-agents`,
  `groundx-studio-harness`, or `adp-poc`
- **WHEN** implementation work is ready to archive
- **THEN** durable requirements have moved into valid OpenSpec changes in the
  owning repos
- **AND** this central change is either closed as planning documentation or
  reduced to only `groundx-python`-owned requirements before archive
- **AND** no cross-repo runtime, API, Arcadia, harness, ADP, or public-docs
  requirement is archived into `groundx-python` as if that repo owned it
