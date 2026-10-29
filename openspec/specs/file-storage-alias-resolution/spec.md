# file-storage-alias-resolution Specification

## Purpose
Shared storage-root resolution without changing ownership or saved URLs.
## Requirements
### Requirement: Aliases are operator-owned configuration

The deployment SHALL use existing `fileAccess.trustedOrigins` for optional alternate origins in the primary file-storage namespace, independently of gateway enablement. Helm SHALL render the corresponding Cashbot YAML, layout Python and extraction Python configuration into the existing Secrets. Aliases SHALL NOT enable protection, declare storage private or change credentials. SDK defaults SHALL contain no hosted GroundX aliases.

#### Scenario: Public on-prem deployment
- **GIVEN** the gateway is disabled and a custom alias is configured
- **WHEN** the chart renders
- **THEN** all applicable consumers receive the alias without creating a gateway or requiring protected-mode readiness settings.

#### Scenario: Separate extraction store
- **GIVEN** extraction overrides the storage endpoint, bucket, backend or region
- **WHEN** its runtime configuration is generated
- **THEN** primary-store aliases are not assigned to that different storage namespace.

### Requirement: SDK resolves configured roots once

`ContainerUploadSettings.url_aliases` SHALL be an optional list of complete HTTP(S) file roots, defaulting to an empty list. Invalid roots with credentials, query, fragment or malformed authority SHALL raise `ValueError` before I/O. `Upload.storage_key(reference: str) -> Optional[str]` SHALL return the exact suffix of the longest matching configured root, or `None` for external URLs and native signed grants. Matching SHALL enforce authority, port and path boundaries; historical HTTP equivalents of configured HTTPS roots SHALL resolve internally without an HTTP request. Root removal SHALL NOT globally decode, normalize or strip the filename/key.

#### Scenario: Mixed hosted addresses
- **GIVEN** a configured current root and older alias for one bucket
- **WHEN** a document source uses the current root and its pages/crops use the alias
- **THEN** all references resolve to their exact keys in that bucket.

#### Scenario: Prefix and signature boundaries
- **GIVEN** roots with path prefixes, overlapping prefixes and explicit ports
- **WHEN** references include lookalike hosts, adjacent path prefixes, another port or a native signature
- **THEN** only complete configured root matches return keys, using the longest prefix
- **AND** signed URLs return `None` without storage I/O.

### Requirement: Cashbot uses one root enumeration

Cashbot SHALL enumerate current presentation, native bucket, public gateway and configured alias roots through one method in `pkg/config/upload.go`. `fileaccess.UploadRoots` and the existing utility/image readers SHALL consume that enumeration. Existing strict URL parsing and legacy stored-filename parsing SHALL retain their different contracts; root recognition SHALL NOT replace authorization or infer ownership from a folder.

#### Scenario: Alias before gateway activation
- **GIVEN** an alias in `fileAccess.trustedOrigins` and file protection disabled
- **WHEN** existing source/image readers resolve that URL
- **THEN** they recognize the same storage namespace as the enabled resolver and preserve their existing read authorization.

#### Scenario: Protected owner check
- **GIVEN** protected images under either current or historical roots
- **WHEN** the existing image authorizer handles owner and wrong-owner requests
- **THEN** the owner reads the same object bytes
- **AND** wrong-owner, deleted or unavailable authorization results do not fall back to anonymous HTTP.

### Requirement: Storage path conventions survive alias resolution

Consumers SHALL add a MinIO/S4 bucket path exactly once, preserve S3 delivery prefixes and retain existing storage-adapter key conventions. Alternate presentation roots SHALL NOT change the configured bucket, region, storage endpoint, stored object names or persisted document URLs. Layout SHALL retain its current string-or-list `uploadReplaceURL` compatibility and existing query-bearing filename semantics.

#### Scenario: Native and delivery roots
- **GIVEN** S3 roots with prefixes or MinIO/S4 roots with and without a bucket suffix
- **WHEN** a saved URL is resolved and passed through the production storage adapter
- **THEN** the adapter requests the original bucket/key, including significant filename bytes and separator handling.

### Requirement: Extraction keeps one authorized image path

Extraction SHALL use the SDK resolver for owned-image selection, current-document validation and key conversion, regardless of `public_read`. Current task/document and authorized-original checks SHALL remain. Public and protected owned images SHALL use the same existing image preparation. Native grants SHALL use exact signed HTTP reads without privileged fallback. Approved external references and supported Bedrock S3/inline choices SHALL retain their existing transports.

#### Scenario: Protected PDF with historical page aliases
- **GIVEN** a protected PDF whose original and page/crop references use different configured roots
- **WHEN** reconcile and QA prepare provider requests
- **THEN** owned images use authorized native reads and the existing provider transport, rather than unsigned remote URLs.

#### Scenario: Public and protected images
- **GIVEN** identical public and protected PNG/JPG originals or PDF pages
- **WHEN** image preparation runs
- **THEN** selected images, bytes and resizing decisions are identical for the same provider budget
- **AND** unrelated-document references remain rejected.

### Requirement: Release preserves generated and deployment boundaries

SDK changes SHALL remain in existing `.fernignore`-protected paths. Compatible binaries/images SHALL precede alias-bearing runtime configuration. Release evidence SHALL distinguish local contract tests, cloud acceptance and deferred live on-prem certification. Rollback SHALL preserve bucket restrictions and existing stored URLs.

#### Scenario: Compatible release ordering
- **WHEN** an SDK release, extraction image and chart are prepared
- **THEN** the chart passes `url_aliases` only when needed and checks compatible SDK support before using a nonempty list
- **AND** no generated API model, package version or new CI workflow is manually edited.
