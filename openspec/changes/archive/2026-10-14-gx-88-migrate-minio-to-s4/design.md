## Goals / Non-Goals

The motivation and current behavior are in `proposal.md`; the required behavior is in `specs/extract-upload-s4/spec.md`.

**Goals:**
- `upload.type: s4` works in the extract upload layer through a new `S4Client(MinIOClient)`. The client signs for `us-east-1` and trims a leading `/` from keys on writes.
- `minio` and `s3` keep selecting the same clients, with the same region and key handling.

**Non-Goals:**
- Write-once uploads. This library's writes send no write-once condition, so the GX-88 single-PUT rule has nothing to apply to here.
- Changes to `S3Client`, to reads, or to the handling of unknown storage types (they still raise).
- Trace capture and Bedrock on non-AWS stores: GX-88 fixes them in cashbot-go and internal-arcadia-agents (ticket amended 2026-10-15); this library needs no change. GX-68 is out of scope.
- Release mechanics. The pull request text carries the release hand-off (`CONTRIBUTING.md` "Release Handoff"); no version field is edited.

## Decisions

**D1. Subclass `MinIOClient` through two hooks: a class attribute and a region method.**
`MinIOClient` gains `upload_type: typing.ClassVar[str] = "minio"`. Its constructor compares `settings.upload.type` with `self.upload_type` instead of the literal `"minio"`. `_create_client` gets its region from a new `_region()` method, which by default returns `self.settings.upload.get_region()`. `S4Client` sets `upload_type = "s4"` and overrides `_region()`. Both hooks default to today's values, so `MinIOClient` keeps its current behavior. GX-88 names this shape for this repository (`S4Client(MinIOClient)`, Linear body, Desired behavior item 4), and so does Ben's comment a39f8d2c ("it could even subclass minio").
- *Alternative:* add `s4` to `MinIOClient` behind `if type in ("minio", "s4")`, with region and key branches inside it. Rejected because it puts S4 rules in the MinIO client, and the ticket asks for a subclass.
- *Alternative:* copy `MinIOClient` into a standalone `S4Client`. Rejected because that duplicates the 445-line `upload_minio.py`, including its timeout and response handling, and the two copies would then drift.

**D2. The region is fixed in `S4Client._region()`, so every minio client it builds uses `us-east-1`.**
Both client paths use `_create_client`: the default client built at construction and the per-timeout clients that `_client_for_timeouts` leases. One override therefore covers both. GX-88 requires S4 mode to use `us-east-1` whatever region is configured, which means `upload.region` and the environment fallbacks are ignored (`src/groundx/extract/settings/settings.py:167-183`). `provision_bucket` needs no override. In the locked minio-py (`minio` 7.2.20, `poetry.lock:2103-2110`), a constructor region is used for every request without a bucket-location lookup (`minio/api.py:487-488`). `make_bucket` sends a `LocationConstraint` only when that region is not `us-east-1` (`minio/api.py:649-658`).
- *Alternative:* set `region="us-east-1"` in the `s4` settings, through the chart or the environment. Rejected because GX-88 says a configured region is ignored, and nothing would stop an environment fallback from overriding it.

**D3. `S4Client` overrides `put_object` and `put_json_stream` to trim a single leading `/`, then delegates.**
Each override has the parent's exact signature. It replaces only `key` (`key[1:]` when the key starts with `/`) and passes every other argument through to `MinIOClient`. "A single leading `/`" follows the GX-88 wording ("a leading `/` is trimmed") and this library's own S3 read path (`upload_s3.py:243-244`). Reads need no change, because `parse_url` already drops the leading `/` (`upload_minio.py:297-318`).
- *Alternative:* a key-normalizing hook on `MinIOClient` used by both writes. Rejected because it would be a third `MinIOClient` change, beyond the two the approved proposal lists. Two small overrides cover the same ground.
- *Alternative:* trim in `MinIOClient` for every mode. Rejected because the proposal keeps `minio` key handling unchanged.

**D4. The dispatcher gains one `elif` branch for `"s4"`, with a lazy import like the existing branches.**
The `minio` and `s3` branches and the final `raise` stay as they are (`upload.py:158-167`). `S4Client` stays out of `groundx.extract.services.__all__`, matching `MinIOClient` and `S3Client` (`services/__init__.py:11-17`).

**D5. Fern boundary: the change stays inside `.fernignore`d paths.**
The edited paths are `src/groundx/extract` (`.fernignore` line 9), `tests/extract` (line 12), `CHANGELOG.md` (line 3), and `openspec` (line 13, so these artifacts survive regeneration). `.fernignore` itself and the Fern-owned version fields (`pyproject.toml`, `src/groundx/core/client_wrapper.py`) do not change. No dependency is added, because `minio` is already in the `extract` extra.

**D6. Tests go in a new `tests/extract/services/test_upload_s4.py` and drive the real `Upload` dispatcher.**
Upload tests here are one file per client (`test_upload_minio.py`, `test_upload_s3.py`), so the S4 tests go beside them, as the approved `proposal.md` and the GX-88 test plan (U16) name. Each test builds `Upload` from `ContainerSettings` and patches only the store client constructors: `minio.Minio` (the existing pattern at `test_upload_minio.py:586`), plus `boto3.client` for the `s3` control. It then asserts what the minio constructor and `put_object` received. Each S4 case is parametrized beside its `minio` counterpart, so a test fails if the S4 rule leaks into `minio` or goes missing from `s4`. `put_object` and `put_json_stream` have separate tests, so removing either trim fails a test. `test_upload.py` and `test_upload_minio.py` are not edited.

**Compatibility (producer):** Additive, re-confirmed against the code. `MinIOClient` gains a class attribute and a method, both defaulting to current behavior. No existing name, signature, or return value changes. A search of internal-arcadia-agents at `ea67325f` found no reference to `MinIOClient`, `upload_minio`, or `S3Client`; `proposal.md` records its `Upload` imports. The compatibility mechanism is the package release: consumers take `s4` support by raising their `groundx` pin. The cross-service shapes live in `contract.md` in the workspace change folder, not here.

No ADR: the change is additive, local to one module family, and reversible.

## Risks / Trade-offs

- [S4 rejects requests signed for `us-east-1`, or a trimmed-key write does not read back through `parse_url`. Unit tests cannot show this, because they stop at the minio constructor and `put_object` arguments.] → This is the external assumption named in `proposal.md`. It was checked on 2026-10-14 against S4 digest 48d1875d outside this repository (GX-88 container test C10, 45/45 assertions in both region modes), not by a committed test, because the repository has no live-store tests in CI.
- [A key that starts with two slashes keeps one after the trim.] → This is accepted to match the GX-88 wording and the S3 read path. `parse_url` would drop both slashes on read, so such a key would not read back on S4. The trim does not cover this case.
- [An extract image built before this release raises `unsupported upload.type [s4]` at start.] → This is a consumer-side ordering concern, handled by the release order in the workspace change (this release, then the internal-arcadia-agents pin, then the image, then the chart).

## Amendments

### 2026-10-16

- **Single PUT on S4.** S4 refuses a key longer than 246 bytes URL-encoded in one PUT and longer than 210 bytes in a multipart upload, each `/` counting 3 bytes (measured by a local probe of S4 image `quay.io/rh-aiservices-bu/s4@sha256:48d1875da2eb087f6b52e01f3e97daa750962a347132230c27d35878c48ce16f` on 2026-10-16). minio-py 7.2.20 sends an object over 5 MiB as a multipart upload. internal-arcadia-agents writes trace files, oversized Celery payloads and the final result (`tasks/save.py:92` at `504c7159`) through `put_json_stream`, and some trace keys are between 211 and 246 bytes, so a trace file over 5 MiB was refused on S4. `MinIOClient` now passes a `part_size` from a new `_part_size(length)` method, which returns `0` (minio-py's default sizing, so `minio` behavior is unchanged). `S4Client._part_size` returns `max(length, MIN_PART_SIZE)`, so minio-py makes one PUT for any object up to 5 GiB, including an empty one, and raises `ValueError` before any request above that. Both write methods take in-memory `bytes`, so no spooling is needed. Requirement "S4Client sends every write as one PUT" in `openspec/specs/extract-upload-s4/spec.md` and tasks 4.1 and 4.2 in `tasks.md` cover it.
- **Superseded lines.** This supersedes the reasoning of the non-goal at `:10` ("the GX-88 single-PUT rule has nothing to apply to here"); write-once uploads stay a non-goal, because this library still sends no write-once condition. It also supersedes "this library needs no change" for trace capture at `:12`, D1's heading "two hooks" at `:17` (`MinIOClient` now has a third, `_part_size`), D3's rejected alternative at `:28` (a third `MinIOClient` change is now made), "gains a class attribute and a method" in Compatibility at `:40`, the "does not apply" sentence at `proposal.md:3`, and "a class attribute and a region method" at `proposal.md:26`. It also supersedes the pointer at `:3` for this behavior (the archived `specs/extract-upload-s4/spec.md` has no single-PUT requirement; it is in `openspec/specs/extract-upload-s4/spec.md`), D6's "patches only the store client constructors" at `:38`, the risk line's "they stop at the minio constructor and `put_object` arguments" at `:46`, and the patched-constructor sentence at `tasks.md:27`: the tests for tasks 4.1 and 4.2 run the real minio-py client and patch only `urllib3.PoolManager.urlopen`. Those lines are left as written.
- **Timeout trade-off on S4.** With one PUT, the caller's transport `total` timeout bounds the whole object instead of each 5 MiB part, so an N MiB write on S4 must connect, upload and get its first response byte inside one timeout window. internal-arcadia-agents (at `504c7159`) uses `total=5.0` seconds for offloaded Celery payloads (`classes/celery_payload.py:21-23`) at most 1.0 second for shared trace files (`classes/pipeline_trace.py:91-93`, `:3893-3905`), and `total=25.0` seconds for the final result (`tasks/save.py:73-75`). This is behavior of the new `s4` type, not a regression: before this change a key over 210 bytes failed outright on S4 for any object over 5 MiB.
