## Why

Protected on-prem file delivery needs extraction workers to connect to private
S3-compatible storage without adding anonymous bucket grants. Legacy worker
configuration must remain compatible.

## What Changes

- Add `ContainerUploadSettings.public_read: bool = True` and optional
  `storage_endpoint: str | None = None` in the hand-written extract layer.
- Private provisioning creates a missing MinIO bucket without a public policy.
  Existing bucket policies are never changed.
- Use an explicit HTTP(S) storage endpoint for connection selection only and
  respect `SSL_CERT_FILE` while keeping certificate verification required.
- Preserve existing credentials, region selection, public presentation URL,
  timeout behavior, storage keys and exact object bytes.

This is an additive package change. No generated API or dependency changes are
required. Design questions: none.

## Capabilities

### New Capabilities
- `extract-private-storage`: compatible private MinIO connection and provisioning.

### Modified Capabilities
None.

## Impact

Edits are limited to `.fernignore`-protected `src/groundx/extract/`,
`tests/extract/` and `openspec/`. GroundX on-prem extraction image builds must
adopt a released SDK containing these constructor fields before enabling the
private Helm settings. Internal Arcadia remains compatible with legacy defaults.
Hosted protection, ownership, presigning and rollout gates belong to
[cashbot-go's producer plan](https://github.com/eyelevelai/cashbot-go/tree/plan/protect-hosted-file-access/openspec/changes/protect-hosted-file-access).
