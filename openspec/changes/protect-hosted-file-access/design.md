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

All local ingest uses `buckets.file_upload` on the configured API, including
public buckets and installations without file protection. The helper does not
read bucket policy to select a signer or fall back to hosted infrastructure.
An explicit `upload_api` (Python) or `uploadApi` (TypeScript) selects the existing
legacy broker protocol for public integrations after an explicit policy read.
Inherited or requested protection rejects an override before any bytes are sent.

Upload expiry limits the native PUT, not the age of an already uploaded public
source. Validate it before PUT, including retries. Do not reject an entire batch
because an earlier successful PUT grant expired before submission. Existing
server ingest admission enforces the binding deadline for protected reservations
and its error reaches the caller unchanged. There is no client policy lookup,
extra response field, renewal, automatic splitting or extra ingest request.

Custom changes stay in `.fernignore`-protected helpers, tests, docs and plans. The protected fixture pack replay covers the current
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

## Generated policy error dispatch

Fern declares the reachable policy errors on existing bucket/document updates and initial-policy operations. Regenerate only the affected clients with the pinned Python generator, preserving handwritten helpers, package version exports and the existing 4.0.9 HTTP headers. Extend the recording HTTP tests to exercise status-specific exceptions in sync and async dispatch while retaining explicit null/revision bodies. Existing full test, aiohttp, extraction replay, mypy, build and LF checks remain required. No extraction runtime, prompts, schemas or routing change, so Arcadia legacy, Arcadia v1, generic v1 and ADP v1 are unaffected. Package publication remains human-owned.

## One upload service

Python `ingest.py` and TypeScript `Wrapper.ts` remain handwritten, protected by
`.fernignore`. Both call the existing generated bucket upload operation for all
ordinary local files, preserving API base URLs, delegated headers and request
options. Native PUT uses only returned storage headers and exact signed URLs. Initial
per-file policy accompanies upload issuance as the canonical optional `fileAccess`
hint, so unavailable protection and ancestor weakening fail before source bytes.
Python uses the generated `file_access` argument and TypeScript uses the
generated request's `fileAccess` field. Both generated surfaces come from normal
full-project Fern generation. Preserve other per-call body options and remove
conflicting upload hint additions so they cannot override the current document's
policy.
Explicit legacy endpoint overrides retain their wire format and metadata
handling without policy discovery. Remote documents and initial policies remain
unchanged. Hosted and on-prem use the same client path; storage selection stays
behind the backend object-store interface. No cloud SDK is added to clients.

Extend the existing upload transport tests for public and protected local API
URLs, failed issuance without fallback, explicit legacy overrides, sync/async,
CSV splits, directory batches, finite PUT lifetime, public submission after a
successful PUT expires, authoritative server admission errors, callbacks and
credential separation.
Keep extraction fixture, generated HTTP and protocol tests in their existing
responsibility files. TypeScript has no owned OpenSpec tree; its wrapper and
existing custom tests are covered by this cross-SDK plan.
