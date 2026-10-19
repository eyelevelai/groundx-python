## Why

The extract upload dispatcher (`src/groundx/extract/services/upload.py:158-167`) accepts only `upload.type` values `minio` and `s3` and raises `unsupported upload.type` for anything else, so constructing `Upload` with `upload.type: s4` raises (`upload.py:167`). GX-88 (Linear body, the authority for this change) makes `s4` a supported storage type in every GroundX service that reads or writes files, and the extract services build their storage through this library. GX-88 requires S4 mode to reuse the MinIO client with fixed differences; two apply here: the region is always `us-east-1` (a configured region is ignored), and a leading `/` is trimmed from keys. The third GX-88 difference, write-once uploads as a single PUT, does not apply: this library's `put_object` and `put_json_stream` send no write-once condition (`upload_minio.py:338-344`, `:432-443`).

## What Changes

- `MinIOClient` (`src/groundx/extract/services/upload_minio.py`): the hard-coded `== "minio"` check at :27 becomes a class attribute whose default is `"minio"`, and the `get_region()` call at :105 moves into an overridable method whose default returns `settings.upload.get_region()` as today. MinIO behavior must not change, and the existing MinIO client tests stay unedited and pass.
- New `S4Client(MinIOClient)` in `src/groundx/extract/services/upload_s4.py`. It sets the type attribute to `"s4"`, always uses region `us-east-1` (ignoring `upload.region` and every environment fallback that `ContainerUploadSettings.get_region()` reads, `src/groundx/extract/settings/settings.py:167-183`), and trims a leading `/` from the key in `put_object` and `put_json_stream`. Reads already drop a leading `/` in `parse_url` (`upload_minio.py:297-318`), so only writes change.
- `Upload` dispatcher (`upload.py:158-167`): `upload.type: s4` selects `S4Client`. `minio` and `s3` select the same clients as before, and any other value still raises.
- Tests in a new `tests/extract/services/test_upload_s4.py`, beside the existing one-file-per-client tests `test_upload_minio.py` and `test_upload_s3.py`. `test_upload.py` and `test_upload_minio.py` are not edited.
- `CHANGELOG.md`: an `### Added` entry under `## Unreleased`.
- No breaking change.

## Capabilities

### New Capabilities

- `extract-upload-s4`: the extract upload layer's `s4` storage type: the dispatcher routes `s4` to `S4Client`; `S4Client` always uses region `us-east-1` and trims a leading `/` from keys on writes; `minio` and `s3` keep selecting their current clients with unchanged behavior. No existing spec in `openspec/specs/` covers the upload dispatcher or its clients.

### Modified Capabilities

None.

## Impact

- **Package surface and semver:** additive only. New module `groundx.extract.services.upload_s4` with `S4Client`; `MinIOClient` gains a class attribute and a region method, both defaulting to the current behavior. `S4Client` is not added to `groundx.extract.services.__all__`, matching `MinIOClient` and `S3Client`, which callers reach through `Upload` (`src/groundx/extract/services/__init__.py:11-17`).
- **Fern boundary:** every edited path is hand-written and listed in `.fernignore` (`CHANGELOG.md` line 3, `src/groundx/extract` line 9, `tests/extract` line 12, `openspec` line 13). The Fern-owned version fields (`pyproject.toml:7`, `src/groundx/core/client_wrapper.py:30,35`), `.fernignore` itself, and the generation source eyelevel-fern-config do not change. No dependency is added: `minio` is already in the `extract` extra (`pyproject.toml:54,121`).
- **Downstream consumers:**
  - internal-arcadia-agents (read at commit `ea67325f`) builds its extract services' storage through `Upload` (`from groundx.extract import ... Upload` in `server.py:7`, `tasks/save.py:8`, and other task modules) and pins `groundx==4.0.7` (`requirements.txt:22`). It must raise that pin to the release that carries `S4Client`, which also brings in every release between 4.0.7 and that one.
  - groundx-on-prem (read at commit `07d332fc`) passes the extract storage type into `upload.type` (`src/groundx/templates/resources/extract-config-py.yaml:106`). It has no code dependency on this package. An extract image older than this release still raises `unsupported upload.type` for `s4`, so the on-prem docs state a minimum version.
  - groundx-studio-harness references this package in docs only (`openspec/config.yaml:49`).
- **Release:** this repository does not publish releases; a human release owner runs the eyelevel-fern-config release workflow (`CONTRIBUTING.md:116-123`). The pull request text carries the release hand-off: it requests version 4.0.10 from that release owner and names the merge commit, the validation evidence, and internal-arcadia-agents as the consumer. The release comes before the internal-arcadia-agents pin, the extract image build, and the on-prem chart publish.
- **Not changed:** `S3Client`; key handling in `MinIOClient` (no trim is added to `minio` mode); handling of unknown storage types (still raises).
- **External assumption:** S4 must accept minio-py requests signed for `us-east-1`, and a write with a trimmed key must read back through `parse_url`. Both are behaviors of S4 that unit tests cannot prove, so they need a check against a real S4 instance.

## Open Questions

None. The approved GX-88 plan settles the client shape, the fixed region, the write-only trim, and the release hand-off.

## Amendments

### 2026-10-19

- **Release version.** The 4.0.10 request in the Release bullet above is historical. main shipped 4.1.0 and 4.1.1 on 2026-10-18 without `S4Client`, so the release hand-off in the pull request now requests 4.1.2. internal-arcadia-agents pins `groundx==4.1.2`.
