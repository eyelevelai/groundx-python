## Design

`ContainerUploadSettings` owns two additive constructor fields. `public_read`
defaults to true, preserving explicit legacy provisioning. `storage_endpoint`
defaults to null, preserving `base_domain` and `ssl` connection selection.
An explicit endpoint must be a full HTTP(S) authority with a valid hostname and
optional port. Credentials, paths, queries, fragments, whitespace and malformed
ports are rejected with `ValueError` through settings validation before storage
I/O. Its authority and scheme override only MinIO endpoint and transport security.

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
presentation field. No signing, URL rewriting, output transformation or new
network call is introduced.

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
