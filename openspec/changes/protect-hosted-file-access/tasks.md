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
- [x] Extend existing sync/async ingest and directory helpers to preserve per-document policies and use bucket-owned staging for public and protected files. Preserve explicit legacy endpoint overrides for public destinations only; fail without hosted fallback on issuance errors.
- [x] Exercise the real generated HTTP transport and existing helpers for inherited protection, explicit file protection in a public bucket, split propagation and public uploads through the configured API. Verify native PUT receives no API credentials and exact signed URL/headers are retained.

Creation-policy validation:694 SDK tests pass,2existing skips,100subtests;156 existing deprecation warnings. Whole-repository mypy passes283 source files. These are local/synthetic results, not storage, release or deployment acceptance.

## Upload grants and ingest admission

- [x] Validate finite upload grants before PUT, including retry attempts.
- [x] Preserve already uploaded public sources after their PUT grant expires.
- [x] Propagate authoritative protected reservation admission failures through
      generated sync/async transport, including CSV splits and directory batches.
- [x] Preserve per-file policies, callbacks and existing batching without client
      renewal, a policy-discovery request or automatic splitting.

The public long-batch regression uses thirty successful thirty-one-second PUTs,
each below the sixty-second request timeout. The SDK submits the resulting stable
public sources even though the first PUT grant has expired. Protected admission
errors come from the API response and retain their status/body; SDK tests do not
emulate server reservation rules. Storage grant expiry is checked again before a
retry. Extraction runtime, prompts, schemas, routing and customer JSON are unchanged.

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
exports even with `--version`. Package metadata remains `4.0.9`.

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

## Generated request metadata

- [x] Retain `client_wrapper.py` byte-for-byte from pushed main
      `c8b14f18a77002c873f8f7550f354b7626f2b674`: `User-Agent` and
      `X-Fern-SDK-Version` report `4.0.9`, and `X-Fern-SDK-Name` reports `groundx`.
- [x] Extend existing sync/async private-ingest transport coverage to compare
      request metadata with the installed package version and public version
      export, retain API/delegated customer keys, and exclude them from native PUT.

The generated wrapper has no change relative to main. `.fernignore`, package
metadata and the initializer's version export are unchanged. No generator
ownership or public API surface is added.

Validation: all four extended transport cases fail on the mismatched
`groundx/4.0.10` user agent before restoration and pass afterward. All 30
upload/export tests pass. The complete SDK suite passes 710 tests with 2 existing
skips, 100 subtests and 156 existing deprecation warnings. Mypy passes all 283
source files; changed-test Ruff lint/format, LF, build and strict OpenSpec checks
pass. All three aiohttp tests and the protected compact replay pass separately.
Arcadia legacy,
Arcadia v1, generic v1 and ADP v1 extraction execution paths are unaffected:
only generated HTTP package metadata is restored, with authentication retained.
These are local checks, not a package release or deployed result.

## Policy error response parity

- [x] Add sync/async recording-transport checks for the errors declared by Fern on updates and initial-policy operations; observe failures before regeneration.
- [x] Regenerate affected clients through the pinned Fern path and retain release metadata and handwritten files.
- [x] Run full SDK/aiohttp suites, protected replay, mypy, changed-file Ruff, build, LF and strict OpenSpec checks.

Local generation root: `openspec/work/protect-hosted-file-access/response-errors`, owned by the SDK maintainer for local pinned SDK generation and validation. Expires 2026-10-19T00:00:00Z; close after reviewed generated clients are retained.

Fern source `ef86e94b29706dac558cb9e2aedb37ffe41b3d33`, CLI `5.37.9` and Python generator `5.10.0` produce the retained bucket/document clients through local filesystem output. The clients match generator bytes; their runtime AST differs only in typed error branches. Existing package metadata, `__version__`, 4.0.9 request headers and handwritten fences remain byte-identical.

Forty-six sync/async recording-transport cases verify typed errors, response bodies, Retry-After and unchanged null/revision bodies. They reproduce generic ApiError before regeneration while customer.update already raises the typed errors. The full SDK suite passes 756 tests with 2 existing skips, 100 subtests and 156 existing deprecation warnings. Aiohttp passes all 3 tests, the protected compact replay passes, and the 4.0.9 wheel/sdist build passes. These are local synthetic checks; no API requests, publication or live acceptance occurs.

Local closeout receipt: `protect-hosted-file-access/response-errors` closed at 2026-10-18T04:55:18.342075+00:00. Removed the exact registered generation/test root and its generator-owned temporary logs, 572 files and 3937402 bytes. Absence verified. The bounded lifecycle summary remains under ignored `openspec/runs`, SHA-256 `fdfbe68a8b8cc4b069d5fdb857073d1c0c9a56b37bb0e633726ffb6d87290bb4`. Reviewed generated clients remain with their SDK owners.

Final exact `poetry run mypy .` after run closeout passes all 283 source files. Changed-test Ruff lint/format, LF, strict OpenSpec and diff checks pass.

## Generated SDK boundary

- [x] Compare every changed generated SDK file with fresh pinned filesystem output from the canonical Fern source; distinguish preserved helper customization.
- [x] Retain package identity through generator-supported full-project output, preserving existing released versions and handwritten fences.
- [x] Extend existing transport coverage only for consequential gaps, run focused SDK checks and close the exact local generation root.

Local generation root: `openspec/work/protect-hosted-file-access/generated-boundary-audit`, owned by the SDK maintainer for pinned generation parity and package-identity validation. Expires 2026-10-19T00:00:00Z. No package publication or live API calls.

Pinned Fern CLI `5.37.9`, Python generator `5.10.0` and TypeScript generator `3.69.0` reproduce every generated runtime change from producer source `ef86e94b29706dac558cb9e2aedb37ffe41b3d33`. Python has 28 byte-identical files and six description-only differences; TypeScript has 42 byte-identical files and six comment-only differences. Current producer `3091a04` adds descriptions only. Full-project filesystem output retains package identity and the Python version export. TypeScript's generated `BaseClient.ts` is restored from that output and matches pushed main byte-for-byte. Handwritten behavior remains within existing `.fernignore` fences.

The existing Python recording-transport tests now cover successful legacy bucket/document updates, omitted/null initial bucket inheritance and page-selector native links. Existing private-ingest coverage already checks parsed 201 uploads and separate native headers. The existing TypeScript delegated-ingest test now checks package identity on API requests; it fails before the generated restoration. Both contributor guides state the local full-project/package-identity requirement.

Validation: exact `poetry run mypy .` passes all 283 source files after generation-root cleanup. Python passes 760 tests with two existing skips, 100 subtests and 156 existing warnings; all three aiohttp tests and the protected compact replay pass separately. TypeScript passes all 480 tests and both CJS/ESM builds. Changed-test Ruff/Biome, LF, strict OpenSpec and diff checks pass. Arcadia legacy, Arcadia v1, generic v1 and ADP v1 extraction runtime, schemas, prompts and routing are unchanged. Package publication and live acceptance remain separate gates.

Local closeout receipt: `protect-hosted-file-access/generated-boundary-audit` closed at 2026-10-18T17:04:48.583001+00:00. Removed the exact registered root and generator-owned temporary roots, 1609 files and 71373966 bytes; absence verified. The bounded lifecycle summary remains under ignored `openspec/runs`, SHA-256 `3f3dd390ea7ea0be6948d39eb7db3c399a46bd102a214bc13ac8e96b54b5b649`.

## One upload service

- [x] Use the existing authenticated bucket upload operation for all local SDK uploads, without policy discovery or hosted fallback.
- [x] Preserve explicit legacy broker overrides and per-file policies, callbacks, splits, batches and delegated request options.
- [x] Extend existing Python and TypeScript transport tests and run SDK validation without editing generated runtime files.

Validation: existing Python upload tests reproduce the old policy lookup before
implementation and pass with the configured API path afterward. The complete
Python suite passes 766 tests, with 2 existing skips, 100 subtests and 156 existing
warnings. The updated HTTP/on-prem grant cases pass all 81 focused upload tests.
Mypy passes 283 files; changed-file Ruff, LF, diff and strict OpenSpec checks pass.
TypeScript has 40 passing custom transport tests and 484 passing tests overall;
CJS and ESM compile, ESM rename, changed-test lint and diff checks pass.

All SDK changes are handwritten paths already preserved by `.fernignore`.
No generated runtime files, generator settings, dependencies or CI change.
Upload tests stay in the existing Python `test_ingest_upload.py` and TypeScript
`custom.test.ts`; provider-specific extraction tests remain separate because they
exercise distinct storage implementations. Extraction prompts, schemas, routing
and final JSON are unchanged, so Arcadia legacy, Arcadia v1, generic v1 and ADP v1
extraction execution paths are unaffected. These local mocked transports do not
prove server deployment, live vendor signing, on-prem connectivity or publication.

## Upload and submission lifetime

- [x] Validate finite upload grants immediately before native PUT, including retry attempts.
- [x] Remove client batch-expiry collectors and pre-submit rejection; preserve long public batches and propagate authoritative protected-source admission errors.
- [x] Extend existing generated-transport tests and document PUT expiry separately from protected reservation admission.

Initial per-file policies accompany upload issuance in the canonical optional
`fileAccess` field, including renewals by browser consumers. Python uses the generated `file_access` argument while preserving unrelated
per-call options; conflicting additional-body hints cannot replace the document's
policy. TypeScript uses the generated request's `fileAccess` field. Explicit
protection rejected by server admission produces no native PUT. The generated
methods and request type are retained from full-project Fern generation.

Final local validation: 84 focused Python upload cases and the complete 769-test
SDK suite pass, with 2 existing skips, 100 subtests and 156 existing warnings.
Mypy passes 283 files. Changed-file Ruff, LF, diff and strict OpenSpec checks
pass. TypeScript passes 41 custom transport cases and 485 tests overall; CJS and
ESM compilation, ESM rename, changed-test lint and diff checks pass. Public long
batches submit after completed PUT grants expire, native retry checks enforce
PUT lifetime, unavailable initial protection stops before bytes, and returned
server admission errors retain status/body. No generated runtime edits, package
publication, deployment or live storage acceptance are included.

## Typed upload hint generation

Local generation root: `openspec/work/protect-hosted-file-access/unified-upload-regeneration`, owned by the SDK maintainer for offline full-project generation from the current canonical Fern source. Expires 2026-10-20T00:00:00Z. Use existing package names and versions, preserve `.fernignore`, retain reviewed generated upload models/clients, then close the exact root with a bounded receipt. No publication or release is authorized.

- [x] Generate Python and TypeScript full projects from the canonical upload request with existing generator settings.
- [x] Use direct generated upload hint parameters in preserved wrappers and extend existing HTTP transport tests.
- [x] Validate generated boundaries, SDK suites and package identity; remove raw generator outputs and retain a bounded closeout receipt.

Full-project generation from Fern `3eb8ca6349dd814a8c36706e3292481b9b8a004d` retains two Python bucket clients and the TypeScript upload request and bucket client. All four files match generator output byte-for-byte. Only the four Python `file_upload` method bodies change at runtime; the TypeScript bucket client has description changes only. Python package exports/headers and TypeScript package headers match full-project output with their existing package versions. Direct typed upload calls preserve omitted, null and protected policies. No publication occurs.

Local closeout receipt: `protect-hosted-file-access/unified-upload-regeneration`, closed 2026-10-18T18:37:04.292789+00:00. State: accepted. Removed the exact registered run root, 640 files and 230753541 bytes; absence verified. Reviewed generated files remain in their owning SDK repos. The bounded local summary is `openspec/runs/protect-hosted-file-access/unified-upload-regeneration.json`, SHA-256 `1f2bcd1e1b379be7028ec23910f9eeb7c408642e9ffe522a247c78e97b27b8d5`. No local run root remains.

## Upload policy response metadata

The upload response optionally includes the existing effective-policy model used
for issuance. Public PUT expiry is not a private ingest deadline. Preserve older
responses without this metadata. No helper transport, request shape, package
version or generator setting changes are required.

Local generation root: `openspec/work/protect-hosted-file-access/upload-policy-response-regeneration`, owned by the SDK maintainer for offline full-project generation from Fern `1c650cd802aa2185e57c87fae85986cb24977de4`. Expires 2026-10-20T00:00:00Z. Retain only affected generated response models, verify existing package identity, close the exact root with a bounded receipt.

- [x] Generate the additive upload response model for Python and TypeScript from canonical Fern.
- [x] Extend existing transport cases for public/protected metadata and omitted legacy metadata.
- [x] Run SDK suites, type/build checks, verify exact generator bytes and close owned artifacts.

Validation: the two response models match full-project generator output byte-for-byte. Python retains 90 focused upload cases and passes 775 tests with 2 existing skips, 100 subtests and 156 existing warnings. Mypy passes 283 files. TypeScript passes 44 custom cases and 488 tests overall, both builds, ESM rename and the explicit custom-test typecheck. Existing package versions, Python exports/headers and TypeScript headers match generator output. No client or wrapper changes are required.

Local closeout receipt: `protect-hosted-file-access/upload-policy-response-regeneration`, closed 2026-10-18T19:11:11.970284+00:00. State: accepted. Removed the exact registered run root, 451 files and 229876321 bytes; absence verified. Reviewed response models remain in their owning SDK repos. The bounded local summary is `openspec/runs/protect-hosted-file-access/upload-policy-response-regeneration.json`, SHA-256 `f5a65eb8ca5dc53f5dac6fc5f43628fc781494297ed70b25beb1fd99d4e67645`. No local run root remains.


## Generated release integration and test preservation

- [x] Integrate the official 4.1.0 release from main, preserving its generated files and package metadata unchanged.
- [x] Verify all pre-change assertions and earlier upload scenarios remain covered in preserved suites.
- [x] Run the full SDK suite, aiohttp, type checks, protected replay and package build.

Local validation root: `openspec/work/protect-hosted-file-access/test-preservation-python`, owned by the SDK maintainer for isolated pytest and build output. Expires 2026-10-20T00:00:00Z. Retain bounded results, then remove this exact root. No publication or live API calls.

The merged producer is Fern `0793e797f33817d5274cb0b763e2fba792212aea`; its successful Python release workflow is `39158722646`. Official release commit `15671152c6d4e8a7dc7a81f0da90f4e8ee6fce8f` supplies every generated file, package 4.1.0 metadata and current protected fixture recordings. All generated files and package metadata match that commit byte-for-byte. Custom behavior and tests remain inside existing `.fernignore` paths, using the configured `GroundXBase` subclasses and exports. No generator settings or versions change.

Test preservation baseline: `c8b14f18a77002c873f8f7550f354b7626f2b674`. All 63 pre-change test functions in the five edited suites remain under their original names; 59 have identical syntax trees. Every prior assertion remains. The four extended cases are the dependency-free client import, legacy hosted-header stripping, transient native PUT retry and bounded MinIO construction cases. The import adds package identity checks, native mocks accept redirect prevention, retry coverage adds expiry without replacing successful retry, and MinIO adds constructor assertions. All other existing tests and generated test scaffolding are unchanged.

| Earlier upload scenario | Current preserved case | Contract |
| --- | --- | --- |
| `test_ingest_reserves_private_source_before_upload` | `test_ingest_uses_configured_api_before_upload` | Sync/async native bytes, initial protection, customer credentials and directory propagation remain. Unified issuance replaces client policy discovery. |
| `test_public_destination_keeps_legacy_upload` | `test_explicit_legacy_upload_override` | Explicit public legacy transport remains; default public transport uses the configured API. |
| `test_failed_policy_lookup_never_falls_back_to_public` | `test_failed_upload_issuance_never_falls_back_to_public` | Issuance failure prevents bytes and hosted fallback. |
| `test_local_batch_checks_private_expiry_before_ingest`, then `test_local_batch_checks_upload_expiry_before_ingest` | `test_local_batch_preserves_submission_and_admission_errors` | Same sync/async public/private/mixed/CSV inputs, counts, callbacks and policy propagation. Protected reservation admission belongs to the server; its 409 status/body is preserved. Public completed PUTs have no batch deadline. |
| `test_monitored_batch_rejects_private_expiry_before_submission`, then `test_monitored_batch_rejects_upload_expiry_before_submission` | `test_monitored_batch_preserves_upstream_admission_error` | Monitored/directory batching preserves the server's admission rejection and stops further submission. |

Validation: 775 tests and 100 subtests pass, with two existing skips; aiohttp passes three tests. Mypy passes all 283 source files. The protected compact fixture replay passes with current main recordings, covering Arcadia legacy, Arcadia v1, generic v1 and ADP v1. The 4.1.0 wheel and sdist build, LF, strict OpenSpec and diff checks pass. No lost test or assertion requires restoration, and no tests, CI jobs, dependencies or schema changes are added. No live API, storage or publication occurs.

Local closeout receipt: `protect-hosted-file-access/test-preservation-python`, closed 2026-10-18T19:34:54.664253+00:00. Accepted; removed the exact registered root (189 files, 2884621 bytes) and verified absence. Bounded local summary SHA-256: `b5c000ca2eba42a344b346937be3c5cb18598a0a9db4df548afdf04eb544fca4`.
