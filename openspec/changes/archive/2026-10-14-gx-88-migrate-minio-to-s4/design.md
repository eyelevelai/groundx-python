## Goals / Non-Goals

The motivation and current behavior are in `proposal.md`; the required behavior is in `specs/extract-upload-s4/spec.md`.

**Goals:**
- `upload.type: s4` works in the extract upload layer through a new `S4Client(MinIOClient)`. The client signs for `us-east-1` and trims a leading `/` from keys on writes.
- `minio` and `s3` keep selecting the same clients, with the same region and key handling.

**Non-Goals:**
- Write-once uploads. This library's writes send no write-once condition, so the GX-88 single-PUT rule has nothing to apply to here.
- Changes to `S3Client`, to reads, or to the handling of unknown storage types (they still raise).
- Trace capture, Bedrock on non-AWS stores, and GX-68 (GX-88 Out of scope).
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

- [S4 rejects requests signed for `us-east-1`, or a trimmed-key write does not read back through `parse_url`. Unit tests cannot show this, because they stop at the minio constructor and `put_object` arguments.] → This is the external assumption named in `proposal.md`. It is checked against a real S4 instance outside this repository (the GX-88 container test of this library's `Upload`), not by a committed test, because the repository has no live-store tests in CI.
- [A key that starts with two slashes keeps one after the trim.] → This is accepted to match the GX-88 wording and the S3 read path. `parse_url` would drop both slashes on read, so such a key would not read back on S4. The trim does not cover this case.
- [An extract image built before this release raises `unsupported upload.type [s4]` at start.] → This is a consumer-side ordering concern, handled by the release order in the workspace change (this release, then the internal-arcadia-agents pin, then the image, then the chart).
