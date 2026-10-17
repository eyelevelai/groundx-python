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

## Creation-time policies and ingest helpers

- [x] Generate optional initial fileAccess models and bucket/file operations from Fern; preserve handwritten files.
- [x] Extend existing sync/async ingest and directory helpers to preserve per-document policies and choose bucket-owned private staging before protected bytes are uploaded. Keep legacy public uploads for unconfigured/public destinations; fail without public fallback on policy or reservation errors.
- [x] Exercise the real generated HTTP transport and existing helpers for inherited protection, explicit file protection in a public bucket, split propagation and unchanged public uploads. Verify native PUT receives no API credentials and exact signed URL/headers are retained.

Creation-policy validation:694 SDK tests pass,2existing skips,100subtests;156 existing deprecation warnings. Whole-repository mypy passes283 source files. These are local/synthetic results, not storage, release or deployment acceptance.

## Reservation expiry before submission

- [x] Retain private upload expiry per batch and reject expired source reservations
      immediately before ingest, with a smaller-batch retry instruction.
- [x] Preserve public upload, initial policies, callbacks and existing single-ingest
      behavior without renewal or automatic batch splitting.
- [x] Cover sync/async, actual CSV splits, mixed public/private uploads, monitored
      batches and directory ingest through the generated HTTP transport.

The expiry regression uses thirty successful thirty-one-second PUTs, each below
the sixty-second request timeout. Expired batches produce no ingest request;
twenty-nine-file fresh batches and public batches retain their existing behavior.
These checks enforce the existing reservation deadline and do not make longer
private batches succeed. Network transit after the local check can still consume
the remaining lifetime. Extraction runtime, prompt policy, schema routing and
customer output are unchanged; historical Arcadia legacy, Arcadia v1, generic v1
and ADP v1 execution paths are unaffected.

Validation: 25 focused upload tests pass. The complete SDK suite in the pinned
Poetry runtime passes 710 tests with 2 existing skips, 100 subtests and 156 existing
extraction YAML deprecation warnings. Whole-repository mypy passes 283 source
files. Changed-file Ruff, LF and strict OpenSpec validation pass. No package,
image, deployment or live storage acceptance follows from these local tests.

## Package version compatibility

- [x] Retain the released package version export in the generated initializer,
      including type-checking, lazy import and wildcard export support.
- [x] Extend the existing isolated base-import test to verify the installed
      metadata version remains available without extract dependencies.

Fern source `aee787cd01340e5f5459594399baf4d3cc68f905`, Python generator
`5.10.0`, and the existing `groundx` version `4.0.9` produce the initializer
with all three version exports when filesystem IR requests a full project.
The isolated generator used `downloadFiles` output with networking disabled;
only its initializer was retained. Ordinary filesystem generation omits these
exports even with `--version`. Package metadata and version headers are unchanged.

Validation: the existing isolated import test fails without the exports and
passes with them; all five export tests pass. The complete SDK suite passes
710 tests with 2 existing skips, 100 subtests and 156 existing deprecation
warnings. The protected compact replay passes independently; all three aiohttp
tests pass. Mypy passes all 283 source files. Changed-file Ruff, LF and strict
OpenSpec checks pass. Extraction runtime, prompt policy, schema routing and
output are unchanged, so Arcadia legacy, Arcadia v1, generic v1 and ADP v1
execution paths are unaffected. These are local checks, not a package release.

Local closeout receipt: `protect-hosted-file-access/version-export-regeneration`
closed on 2026-10-17 at 18:15 UTC. The dedicated work root and generator-owned
temporary outputs were removed (742 files, 27,650,199 bytes); absence was verified.
The lifecycle-only summary remains under ignored `openspec/runs`, SHA-256
`ee4f2f056c79f39f63ae87d2092ab421acfae6bdd27851080ec54ad832ce6855`.
