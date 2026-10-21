# extract-upload-s4 Specification

## Purpose
TBD - created by archiving change gx-88-migrate-minio-to-s4. Update Purpose after archive.
## Requirements
### Requirement: Upload selects S4Client for the s4 storage type
`groundx.extract.services.Upload(settings, logger)` SHALL set its `client` to an `S4Client` (module `groundx.extract.services.upload_s4`) when `settings.upload.type` is `"s4"`. `S4Client` is a subclass of `MinIOClient`. It SHALL build its minio client at construction when `settings.upload.type` is `"s4"`, the same way `MinIOClient` builds one when the type is `"minio"`; for any other type its `client` attribute stays `None`, as `MinIOClient`'s does today. `Upload` SHALL keep selecting `MinIOClient` for `"minio"` and `S3Client` for `"s3"`, and SHALL still raise `Exception("unsupported upload.type [<value>]")` for any other value, before constructing any storage client, as it does today. Type matching stays exact and case-sensitive, as it is for `"minio"` and `"s3"`. `S4Client` is not added to `groundx.extract.services.__all__`; callers reach it through `Upload`, as they reach `MinIOClient` and `S3Client`.

#### Scenario: s4 selects S4Client with a live minio client
- **Polarity:** accept and enqueue: the value is accepted and handed to `S4Client`, never rejected and never left without a client
- **WHEN** `Upload` is constructed with `settings.upload.type` set to `"s4"`
- **THEN** `upload.client` is an `S4Client`
- **AND** `upload.client.client` is the minio client built at construction, not `None`
- **AND** the constructor does not raise `unsupported upload.type [s4]`

#### Scenario: minio and s3 keep selecting their existing clients during rollout
- **Polarity:** skip unrelated repair path: existing storage types are not routed through `S4Client`
- **WHEN** `Upload` is constructed with `settings.upload.type` set to `"minio"`, or to `"s3"`
- **THEN** `upload.client` is exactly a `MinIOClient` (not an `S4Client`) for `"minio"`, and exactly an `S3Client` for `"s3"`

#### Scenario: an unknown storage type is still rejected before any client is built
- **Polarity:** reject before state: no minio or boto3 client is constructed for the rejected value
- **WHEN** `Upload` is constructed with `settings.upload.type` set to a value other than `"minio"`, `"s3"`, or `"s4"`, for example `"gcs"`
- **THEN** the constructor raises `Exception` with the message `unsupported upload.type [gcs]`
- **AND** no minio client and no boto3 client was constructed

### Requirement: S4Client signs every request for us-east-1
`S4Client` SHALL construct every minio client it creates, both the default client and each per-timeout client used by bounded reads and writes, with `region="us-east-1"`. It SHALL ignore `settings.upload.region` and every environment fallback that `ContainerUploadSettings.get_region()` reads (`GROUNDX_REGION`, `AWS_REGION`, `GROUNDX_DEFAULT_REGION`, `AWS_DEFAULT_REGION`). `MinIOClient` SHALL keep constructing its minio clients with `settings.upload.get_region()`, unchanged.

#### Scenario: a configured region is ignored in s4 mode
- **Polarity:** finalize success: the client is built for `us-east-1`, never for the configured region
- **WHEN** `Upload` is constructed with `settings.upload.type` `"s4"` and `settings.upload.region` `"us-west-2"`, and then performs a bounded `put_json_stream`
- **THEN** every minio client it constructed received `region="us-east-1"`
- **AND** no minio client received `region="us-west-2"`

#### Scenario: environment region fallbacks are ignored in s4 mode
- **Polarity:** finalize success: the environment does not change the signing region
- **WHEN** `settings.upload.region` is unset, `GROUNDX_REGION`, `AWS_REGION`, `GROUNDX_DEFAULT_REGION`, and `AWS_DEFAULT_REGION` are all `"us-west-2"`, and `Upload` is constructed with type `"s4"` and then performs a bounded `put_json_stream`
- **THEN** both the default client and the per-timeout client received `region="us-east-1"`

#### Scenario: minio mode keeps the region from settings and the environment
- **Polarity:** skip unrelated repair path: the fixed s4 region is not applied to `minio`
- **WHEN** `settings.upload.region` is unset, the region environment variables are `"us-west-2"`, and `Upload` is constructed with type `"minio"` and then performs a bounded `put_json_stream`
- **THEN** both minio clients received `region="us-west-2"`

### Requirement: S4Client trims a single leading slash from keys on writes
`S4Client.put_object` and `S4Client.put_json_stream` SHALL remove a single leading `/` from `key` before writing, and SHALL pass `bucket`, `data`, `content_type`, the timeout arguments, and `object_tags` to the `MinIOClient` write unchanged. A key that does not start with `/` SHALL be written as given. Reads (`get_object`, `get_object_and_metadata`, `head_object`) keep their current key handling, because `parse_url` already drops a leading `/`. `MinIOClient` writes keys exactly as given; no trim is added in `minio` mode.

#### Scenario: put_object writes the trimmed key in s4 mode
- **Polarity:** finalize success: the object name sent to the store never keeps the leading slash
- **WHEN** an `Upload` of type `"s4"` calls `put_object("eyelevel", "/layout/processed/doc.json", data, "application/json")`
- **THEN** the minio client's `put_object` receives `object_name="layout/processed/doc.json"`
- **AND** it does not receive `object_name="/layout/processed/doc.json"`

#### Scenario: put_json_stream writes the trimmed key and keeps tags and timeouts in s4 mode
- **Polarity:** finalize success: the trim changes only the key
- **WHEN** an `Upload` of type `"s4"` calls `put_json_stream("eyelevel", "/layout/processed/doc.json", data, "application/json")` with connect, read, and transport-total timeouts and `object_tags`
- **THEN** the minio client's `put_object` receives `object_name="layout/processed/doc.json"` and the same tags
- **AND** the write uses a per-timeout minio client configured with the caller's transport-total timeout

#### Scenario: a key without a leading slash is written as given in s4 mode
- **Polarity:** skip unrelated repair path: a key that needs no trim is not altered
- **WHEN** an `Upload` of type `"s4"` writes with `put_object` or `put_json_stream` using the key `"layout/processed/doc.json"`
- **THEN** the minio client receives `object_name="layout/processed/doc.json"`

#### Scenario: minio mode writes keys exactly as given
- **Polarity:** skip unrelated repair path: the s4 trim is not applied to `minio`
- **WHEN** an `Upload` of type `"minio"` writes with `put_object` or `put_json_stream` using the key `"/layout/processed/doc.json"`
- **THEN** the minio client receives `object_name="/layout/processed/doc.json"`

### Requirement: S4Client sends every write as one PUT
`S4Client.put_object` and `S4Client.put_json_stream` SHALL send each object of up to 5 GiB to the store as one PUT request, never as a multipart upload, because S4 accepts a longer key in one PUT (246 bytes URL-encoded) than in a multipart upload (210). An object larger than 5 GiB SHALL be refused with a `ValueError` before any request is sent. `MinIOClient` SHALL keep minio-py's default sizing, so an object over 5 MiB still goes as a multipart upload in `minio` mode.

#### Scenario: an object over 5 MiB goes as one PUT in s4 mode
- **Polarity:** finalize success: the store receives one PUT and no multipart initiate
- **WHEN** an `Upload` of type `"s4"` writes a 6 MiB object with `put_object` or `put_json_stream`
- **THEN** the store receives exactly one `PUT` with no `uploads`, `uploadId`, or `partNumber` query

#### Scenario: an object under 5 MiB goes as one PUT in s4 mode
- **Polarity:** finalize success: the store receives one PUT
- **WHEN** an `Upload` of type `"s4"` writes a 0-byte or 4 KiB object with `put_object` or `put_json_stream`
- **THEN** the store receives exactly one `PUT` with no `uploads`, `uploadId`, or `partNumber` query

#### Scenario: an object over 5 GiB is refused before any request in s4 mode
- **Polarity:** reject before state: nothing is sent to the store
- **WHEN** an `Upload` of type `"s4"` writes an object longer than 5 GiB with `put_object` or `put_json_stream`
- **THEN** the write raises `ValueError`
- **AND** no request reaches the store

#### Scenario: minio mode keeps multipart for an object over 5 MiB
- **Polarity:** skip unrelated repair path: the s4 single PUT is not applied to `minio`
- **WHEN** an `Upload` of type `"minio"` writes a 6 MiB object with `put_object` or `put_json_stream`
- **THEN** the store receives a multipart initiate, two part uploads, and a complete request
