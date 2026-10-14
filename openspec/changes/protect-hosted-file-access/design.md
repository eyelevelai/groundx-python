## Design

`ContainerUploadSettings` owns two additive constructor fields. `public_read`
defaults to true, preserving explicit legacy provisioning. `storage_endpoint`
defaults to null, preserving `base_domain` and `ssl` connection selection.
An explicit endpoint must be a full HTTP(S) authority with a valid hostname and
optional port. Credentials, non-root paths, queries, fragments, whitespace and malformed
ports are rejected with `ValueError` through settings validation before storage
I/O. Its authority and scheme override only MinIO endpoint and transport security.
An optional root slash is accepted; no non-root path is accepted.

MinIO construction remains free of provisioning. `provision_bucket` checks
existence, creates only missing buckets and installs the existing anonymous
read policy only when `public_read` is true. It never modifies existing grants,
including in private mode. Existing public buckets therefore need a separately
authorized deployment policy audit and migration.

All MinIO clients, including clients cached for explicit timeouts, use the same
endpoint selection and TLS trust. HTTPS sets `CERT_REQUIRED`; nonempty
`SSL_CERT_FILE` selects the CA bundle, otherwise the current certifi default
remains. HTTP keeps the existing non-TLS behavior. Credentials and region retain
their existing explicit-value then environment precedence. `url` remains a
presentation field. Storage settings do not add signing, URL rewriting or output
transformation.

Only `src/groundx/extract/`, `tests/extract/` and `openspec/` are edited, all
preserved by `.fernignore`. The protected fixture pack replay covers the current
promoted cases; storage changes do not change extraction placement, candidate
selection or customer JSON contracts. Required historical Arcadia v1, generic
v1 and ADP v1 surfaces remain unaffected because their parser/reassembly paths
are untouched; promoted compact replay and the complete extract tests protect
the currently maintained surfaces.

Rollout requires an SDK release by the human release owner and a downstream
extraction image containing that exact release. Local mocks do not prove live
TLS, anonymous-origin denial, MinIO/AIStor/S4 compatibility or deployed behavior.
Those remain producer/on-prem activation gates. Rollback uses a compatible SDK
when private Helm settings are active; do not restore public policies implicitly.

## Protected HTTP consumers

The existing `GroundXDocument.xray` and `XRayDocument.download` gain keyword-only
`xray_url`, `api_key`, `customer_key` and `trusted_file_roots` arguments.
`DocumentRequest.load_images` gains the same credential/trust arguments. Defaults
retain existing public and internal object-store behavior. No environment key is
implicitly selected for a returned URL.

One `bounded_file_get` helper in `services/http.py` uses the existing bounded
transport. Explicit trusted roots must be HTTPS URLs without credentials,
query or fragment. A target must match the configured authority and path prefix
at a segment boundary before it can receive `X-API-Key` and optional delegated
`X-Customer-Key`. Native signed URLs receive neither header, even when their host
matches a root. Opt-in reads do not follow redirects. Response bodies stream
under the existing deadline/close mechanism before consumer parsing; headers,
query grants and keys are omitted from error/log URLs.

An explicit returned `xray_url` is fetched unchanged and bypasses disk cache and
object-store shortcuts. Each call therefore refreshes `?view=links` asset
references; no rewritten X-Ray bundle is persisted. Native signed image URLs
also bypass the privileged object-store shortcut and keep their exact query.
Configured authenticated image readers use HTTP authorization instead of service
credentials. There is no HEAD probe and no new issuer or automatic metadata
client. After expiry, the application downloads fresh presentation or obtains a
new native link and calls the existing reader again.

Actual browser QC is owned by
`groundx-ai-dashboard/src/api/entities/demo.ts:getTrainedDocument`; Harness QC
capture/download is owned by the extraction certification templates. Arcadia's
provider-size HEAD probe is in `internal-arcadia-agents/classes/image_evidence.py`.
Those consumers require separate owner changes; an SDK helper cannot establish
their adoption. This patch does not change extraction values, prompt policy,
route placement, stored X-Ray or final JSON.
