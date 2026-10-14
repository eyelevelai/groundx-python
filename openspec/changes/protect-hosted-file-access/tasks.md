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

## Protected consumers

- [x] Add returned-URL and explicit credential/trust arguments to existing X-Ray
      and page-image readers, with one narrow bounded GET helper.
- [x] Enforce HTTPS root matching, native-grant header exclusion and redirect
      rejection; close streaming responses within bounded body-read deadlines.
- [x] Bypass disk/object-store caches for returned X-Ray URLs and privileged
      storage shortcuts for native signed image GETs.
- [x] Cover public compatibility, owner/delegated headers, wrong hosts/paths,
      redirects, exact signatures, expired grants, fresh presentation and log
      redaction without changing fixtures or extraction outputs.
- [x] Run focused tests, required compact replay, complete SDK suite, mypy,
      changed-file Ruff, build, LF and strict OpenSpec gates.
- [x] Record SDK validation and separate application adoption/live gates.

Consumer validation: 69 focused tests pass; the complete SDK suite with extract
and aiohttp extras passes 687 tests with 2 existing skips, 100 subtests and
156 existing deprecation warnings. The protected compact fixture replay passes
independently. Mypy reports no issues in 267 source files. Changed-file Ruff,
build, LF and strict OpenSpec gates pass. All HTTP credentials and expiry cases
use controlled test responses; no live protection or application adoption is
established by these tests.
