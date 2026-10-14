## Implementation

- [x] Add private provisioning and unchanged legacy/existing-bucket regression coverage.
- [x] Add explicit endpoint validation and connection selection coverage.
- [x] Add custom CA, timeout-client and exact-byte storage coverage.
- [x] Implement the two additive settings and shared MinIO connection behavior.
- [x] Run storage/settings tests, complete extract tests, protected compact fixture
      replay, changed-file Ruff, mypy, build and line-ending checks.
- [x] Record validation evidence and downstream release/image adoption gates.

## Validation

- Focused storage/settings suite: 65 passed, 32 subtests passed.
- Complete extract suite: 547 passed, 1 pre-existing AGE-68 skip,
  100 subtests passed.
- Protected compact fixture replay: 1 passed, including all five promoted cases
  (Arcadia legacy, Energy v2, generic v2, ADP v4, Warner Armstrong).
- Complete SDK suite with extract dependencies: 649 passed, 5 existing skips.
- Complete SDK suite with extract and aiohttp dependencies: 652 passed,
  2 existing skips, 100 subtests passed. Both complete suites report 156 existing
  extraction YAML deprecation warnings. Remaining skips are the unimplemented
  custom client test and quarantined AGE-68 empty-number behavior.
- `poetry run mypy .`: no issues in 266 source files.
- Changed-file Ruff lint/format, `poetry build`, LF checks, `git diff --check`
  and strict OpenSpec validation pass.

These are local tests with storage I/O mocked. They do not establish live vendor
compatibility, private-origin denial, custom-CA connectivity or deployed image
adoption.

## Release

- [ ] Human SDK release owner publishes the merged hand-written change through
      the established Fern release path.
- [ ] GroundX on-prem extraction image adopts the compatible SDK version and
      passes live private-storage and CA verification before activation.
