# extract-private-storage Specification

## Purpose
Credentialed extraction storage and explicit bucket provisioning.
## Requirements
### Requirement: MinIO provisioning preserves public compatibility and private intent

`ContainerUploadSettings` SHALL accept `public_read: bool`, defaulting to true.
MinIO initialization SHALL NOT provision storage. Explicit provisioning SHALL
create only missing buckets and SHALL add an anonymous read policy only when
`public_read` is true. It SHALL NOT change existing bucket policies.

#### Scenario: Private missing bucket
- **GIVEN** `public_read` is false and the configured bucket is missing
- **WHEN** `provision_bucket` is called
- **THEN** the bucket is created without an anonymous read policy.

#### Scenario: Legacy missing bucket
- **GIVEN** `public_read` is omitted and the configured bucket is missing
- **WHEN** `provision_bucket` is called
- **THEN** the current anonymous read policy is installed on the new bucket.

#### Scenario: Existing bucket
- **GIVEN** the bucket already exists, in either mode
- **WHEN** construction or explicit provisioning occurs
- **THEN** no creation or policy mutation occurs.

### Requirement: Private connection settings do not change presentation or credentials

`ContainerUploadSettings` SHALL accept nullable `storage_endpoint`, defaulting
to null. A non-null value SHALL be an HTTP(S) URL containing only a valid host
and optional port. Invalid schemes, credentials, paths, query, fragment,
whitespace and malformed ports SHALL fail settings validation with `ValueError`.
An explicit endpoint SHALL select MinIO authority and TLS only; otherwise
`base_domain` and `ssl` SHALL retain their current behavior. `url`, object keys,
region and credential precedence SHALL remain unchanged.

#### Scenario: Explicit private connection
- **GIVEN** a public presentation URL and an HTTPS private storage endpoint
- **WHEN** default and timeout-specific MinIO clients are constructed
- **THEN** both use the private authority and TLS with existing credentials and region
- **AND** reads and writes preserve exact bytes and keys.

#### Scenario: Malformed endpoint
- **GIVEN** an endpoint contains credentials, a path, a query, a fragment or an invalid authority
- **WHEN** upload settings are constructed
- **THEN** validation fails before a storage client is created.

### Requirement: HTTPS uses the configured CA with verification required

Every HTTPS MinIO client SHALL use nonempty `SSL_CERT_FILE` when supplied,
otherwise certifi's default bundle, and SHALL keep `CERT_REQUIRED`.

#### Scenario: Private certificate authority
- **GIVEN** HTTPS storage and `SSL_CERT_FILE` pointing to a custom trust bundle
- **WHEN** default and timeout-specific clients are constructed
- **THEN** each transport uses that bundle with certificate verification required.

#### Scenario: Legacy CA fallback
- **GIVEN** HTTPS storage and no nonempty `SSL_CERT_FILE`
- **WHEN** a client is constructed
- **THEN** certifi's bundle is used with certificate verification required.
