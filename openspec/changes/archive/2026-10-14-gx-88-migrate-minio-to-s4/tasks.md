## 1. Route `upload.type: s4` to S4Client, signing for us-east-1 (first end-to-end slice)

- [x] 1.1 In `src/groundx/extract/services/upload_minio.py`, give `MinIOClient` the class attribute `upload_type: typing.ClassVar[str] = "minio"` and compare `settings.upload.type` with `self.upload_type` in the constructor. Add `src/groundx/extract/services/upload_s4.py` with `S4Client(MinIOClient)`, which sets `upload_type = "s4"`. Add an `"s4"` branch to the `Upload` dispatcher (`src/groundx/extract/services/upload.py:158-167`) with a lazy import, like the existing branches. Leave the `minio`, `s3`, and `raise` branches unchanged (design D1, D4).
  check: poetry run pytest "tests/extract/services/test_upload_s4.py::test_upload_type_s4_selects_s4_client_with_a_live_minio_client" "tests/extract/services/test_upload_s4.py::test_minio_and_s3_upload_types_keep_their_clients" "tests/extract/services/test_upload_s4.py::test_upload_rejects_an_unknown_upload_type_before_building_a_client" tests/extract/services/test_upload.py -q
- [x] 1.2 Replace the `self.settings.upload.get_region()` argument in `MinIOClient._create_client` with a new `_region()` method that returns `self.settings.upload.get_region()`. Override `_region()` in `S4Client` to return `"us-east-1"` (design D2).
  check: poetry run pytest "tests/extract/services/test_upload_s4.py::test_s4_signs_for_us_east_1_and_minio_keeps_the_configured_region" tests/extract/services/test_upload_minio.py -q

## 2. Trim a single leading slash from S4 write keys

- [x] 2.1 Override `S4Client.put_object` with exactly the parent's signature. It removes a single leading `/` from `key` and delegates to `MinIOClient.put_object` (design D3).
  check: poetry run pytest "tests/extract/services/test_upload_s4.py::test_put_object_trims_a_leading_slash_only_in_s4_mode" -q
- [x] 2.2 Override `S4Client.put_json_stream` with exactly the parent's signature. It removes a single leading `/` from `key` and passes `bucket`, `data`, `content_type`, every timeout argument, and `object_tags` to `MinIOClient.put_json_stream` unchanged (design D3).
  check: poetry run pytest "tests/extract/services/test_upload_s4.py::test_put_json_stream_trims_a_leading_slash_only_in_s4_mode_and_keeps_tags_and_timeouts" -q

## 3. Changelog

- [x] 3.1 In `CHANGELOG.md`, under `## Unreleased`, add an `### Added` section above `### Deprecated`. It states that `upload.type: s4` selects the new `S4Client` (`groundx.extract.services.upload_s4`, a `MinIOClient` subclass). It also states that `S4Client` always signs for `us-east-1`, ignoring `upload.region` and the region environment variables, that it trims a leading `/` from keys on `put_object` and `put_json_stream`, and that `minio` and `s3` behave as before.
  check: n/a — changelog text, no runtime behavior

The acceptance tests named above live in `tests/extract/services/test_upload_s4.py`. They drive the real `Upload` dispatcher with only `minio.Minio` (and `boto3.client` for `s3`) patched. `tests/extract/services/test_upload.py` and `tests/extract/services/test_upload_minio.py` are not edited.

Consumer pin: internal-arcadia-agents pins `groundx==4.0.7` (`requirements.txt:22` at `ea67325f`). It must raise that pin to the release that carries `S4Client`; the pull request's release hand-off requests 4.0.10. See workspace `openspec/changes/gx-88-migrate-minio-to-s4/tasks.md` for cross-service coordination and deferred items.
