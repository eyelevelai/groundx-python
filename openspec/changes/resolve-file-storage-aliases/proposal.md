## Why

Extraction checks one configured hostname, but stored X-Ray page and crop URLs can use an older hostname for the same bucket. Cashbot's gateway supports configured aliases, while several older Go URL helpers enumerate a different set of roots. These differences can send a protected image to a model as an unsigned URL or resolve the wrong storage path.

## What Changes

- Reuse the existing operator setting `fileAccess.trustedOrigins`; distribute it to Cashbot, layout and extraction for the same storage namespace, including public deployments with the gateway disabled.
- Centralize Cashbot's root enumeration in its existing `config.Upload` code. Retain the gateway's existing resolver and authorization; update legacy utility and image readers to consume the same root list.
- Add optional `ContainerUploadSettings.url_aliases` and `Upload.storage_key(reference)` in the handwritten SDK. Extraction image selection, scope validation and storage reads reuse this method.
- Retain layout's existing `File.storageKey` implementation and provide its existing `uploadReplaceURL` setting with the corresponding alias list.
- Extend existing tests and operator/contributor documentation. No new runtime service, cache, table, public API, queue or CI workflow.

## Capabilities

### New Capabilities

- `file-storage-alias-resolution`: Consistent configured storage identity across hosted and on-prem URL consumers, preserving document authorization and signed-link authority.

### Modified Capabilities

None. Existing protected HTTP readers, policy inheritance, upload issuance and file-link APIs retain their contracts.

## Impact

Implementation owners: groundx-python, cashbot-go, internal-arcadia-agents and groundx-on-prem. ai-server needs configuration/documentation alignment and existing-reader regression coverage, not another resolver. groundx-studio-harness needs operator/reference updates. The generated public harness follows its normal source synchronization.

The SDK addition is optional and backward compatible. Handwritten source, tests and OpenSpec are already protected by `.fernignore`; generated SDK files and package versions are unchanged. A human-owned SDK release precedes the extraction image and chart change. Cashbot uses its existing Lambda/server build paths. Workspace runner, TypeScript clients, Fern schemas, dashboard and middleware do not gain a new URL resolver because their relevant paths return or consume existing API links, not extraction storage keys.

No SQL, stored-link migration, DNS, IAM, bucket-policy or infrastructure changes are proposed. Hosted saved configuration changes require an exact sanitized diff and approval before application. Deployment uses rolling updates and rollback to the recorded prior image/configuration; no global API or ingestion pause.

## Open Questions

None for the implementation design. The exact hosted configuration resources, release versions and image digests must be inventoried before deployment; planning does not authorize deployment.
