# extraction-fixture-replay Specification

## Purpose
Pin groundx-python's share of the cross-repo extraction certification
contract: the promoted compact fixture pack installed at
`tests/extract/fixtures/extraction-fixture-pack` and the protected reassembly
replay that exercises it in standard CI. The pack's lifecycle (capture,
review, promotion, registry binding) is governed by the GroundX Studio Harness
certification tooling; this repo consumes one promoted candidate and must fail
loudly when it is missing, incomplete, or unapproved.

## Requirements

### Requirement: Protected replay runs in standard CI

`groundx-python` SHALL replay every configured case of the installed compact
fixture pack through `reassemble_custom_outputs_from_xray` in the standard
test suite (`tests/extract/test_compact_fixture_pack_replay.py`), asserting
outputs, diagnostics, and source provenance against the pack's reviewed blobs
and validating each X-Ray input as a canonical live-capture predecessor.

#### Scenario: Reassembly behavior changes

- **WHEN** a change alters reassembly output for a certified case
- **THEN** the protected replay fails in standard CI

### Requirement: Replay fails closed on pack state

The replay SHALL fail when the installed pack is missing, is not promoted, is
not approved, or does not carry exactly its configured case set.

#### Scenario: A case disappears from the installed pack

- **WHEN** the installed pack loses one configured case
- **THEN** the replay fails before any case is exercised

### Requirement: Publishing requires the protected replay to exist

The release preflight SHALL fail when the protected replay test or the
installed fixture pack is absent, so deleting either can never leave
publishing unblocked.

#### Scenario: The replay test is deleted

- **WHEN** `tests/extract/test_compact_fixture_pack_replay.py` or the
  installed pack is removed
- **THEN** `tests/custom/test_release_preflight.py` fails in standard CI
