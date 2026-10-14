## ADDED Requirements

### Requirement: Existing HTTP readers support explicit protected presentation

`GroundXDocument.xray` and `XRayDocument.download` SHALL accept keyword-only
nullable `xray_url`, `api_key`, `customer_key` and optional `trusted_file_roots`.
`DocumentRequest.load_images` SHALL accept the credential/trust arguments.
Defaults SHALL retain current public and internal-storage behavior. An explicit
X-Ray URL SHALL be fetched unchanged without disk cache read/write or privileged
object-store fallback. Customer context without an API key SHALL fail with
`ValueError`.

#### Scenario: Presentation refresh
- **GIVEN** returned X-Ray `?view=links` and an existing cached raw X-Ray
- **WHEN** the caller downloads presentation twice
- **THEN** each call retrieves fresh asset references over HTTP
- **AND** the cached raw X-Ray is neither read nor overwritten.

#### Scenario: Public legacy reader
- **GIVEN** no new arguments are configured
- **WHEN** the existing reader downloads X-Ray or page images
- **THEN** existing URL, cache and credentialed worker behavior is retained.

### Requirement: Keys are limited to explicit trusted HTTPS roots

`bounded_file_get` SHALL attach `X-API-Key` and optional delegated
`X-Customer-Key` only to configured trusted HTTPS authority/path roots.
Credentials, query and fragment in a root SHALL raise `ValueError` before I/O.
Target credentials, malformed authorities and path traversal SHALL NOT receive
keys. Matching SHALL require path-segment boundaries. Native storage signatures
SHALL exclude GroundX headers even when the storage host overlaps trusted roots.
Configured reads SHALL disable redirects and reject 3xx responses. Response
bodies SHALL use streaming transport and close under the existing body deadline.
Errors and reader logs SHALL omit keys and signature query values.

#### Scenario: Delegated protected read
- **GIVEN** a configured HTTPS gateway root, partner API key and customer context
- **WHEN** an owned hosted asset is requested beneath that root
- **THEN** the request carries the two existing authentication headers.

#### Scenario: Wrong destination
- **GIVEN** a returned URL on an unconfigured host, a different port or outside the trusted path
- **WHEN** the URL is fetched
- **THEN** neither GroundX header is attached.

#### Scenario: Redirect cannot forward credentials
- **GIVEN** a trusted gateway returns a redirect to native storage or another host
- **WHEN** a configured read receives that response
- **THEN** the redirect is rejected without a second credential-bearing request.

### Requirement: Native grants remain exact GET grants

Readers SHALL preserve the supplied native signed URL and query, SHALL perform
GET without HEAD preflight and SHALL bypass privileged object-store shortcuts.
An expired grant SHALL NOT be retried with GroundX/service credentials. The caller
SHALL refresh X-Ray presentation or obtain a new link before retrying. No new
sharing token, stored presentation bundle or output/prompt/routing contract is
introduced.

#### Scenario: Native signed image
- **GIVEN** a signed image GET URL and an available worker upload adapter
- **WHEN** the image is downloaded
- **THEN** the exact URL is sent to HTTP GET without GroundX headers
- **AND** the upload adapter and HEAD are not used.

#### Scenario: Expired native grant
- **GIVEN** an expired asset link fails storage verification
- **WHEN** the caller retrieves fresh gateway X-Ray presentation and retries its new link
- **THEN** only the fresh link is used with its native signature
- **AND** no privileged fallback occurs.
