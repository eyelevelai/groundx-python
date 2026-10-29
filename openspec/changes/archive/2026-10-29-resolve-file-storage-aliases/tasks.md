## 1. SDK resolver and consumer

- [x] 1.1 Extend `tests/extract/services/test_upload.py` and existing settings tests with current/alias roots, HTTPS historical equivalents, native signatures, invalid roots, path prefixes, exact filename bytes and ports. Reproduce the current missing alias behavior before implementation.
- [x] 1.2 Add optional `ContainerUploadSettings.url_aliases` and `Upload.storage_key(reference: str) -> Optional[str]` in existing files, reusing the native signature detector. Assert exact keys through maintained S3/MinIO/S4 adapter tests; keep existing constructor defaults and get/read timeout contracts.
- [x] 1.3 Extend `tests/extract/classes/test_document.py`, then adopt the resolver in `DocumentRequest.load_images`. Preserve explicit protected HTTP transport and terminal native-signature/authorization failures. Run focused tests, existing extract suite/replays, mypy, build and LF checks required by the repo.

## 2. Cashbot shared roots and readers

- [x] 2.1 Extend `pkg/utility/stored_source_test.go`, `url_test.go` and existing `pkg/fileaccess/resolve_test.go` tables with a trusted alias absent from current/native roots. Exercise `StoredSourceKey`, `IsInternalURL`, `RemoveBaseURL`, `SwapBucketURL` and the resolver using both feature states and S3/MinIO/S4 prefixes. Record each current failure before fixing it.
- [x] 2.2 Add `func (u Upload) FileRoots(f FileAccess) []string` in `pkg/config/upload.go`; make `fileaccess.UploadRoots` attach identities to that list. Reuse `bucketURL` for bucket suffixes. Extend existing config tests; add no config field or package.
- [x] 2.3 Update existing utility prefix/key helpers to use the shared list and longest complete leading root. Keep exported signatures, relative-key behavior, exact legacy filename parsing and native grants. Assign primary aliases only to their configured namespace, preserving distinct UploadGroundX roots.
- [x] 2.4 Extend existing `pkg/fileaccess/transport_test.go`, `pkg/prompt/multimodal_test.go` and ratelimit image tests. Run production image preparation through authorized aliases, historical HTTP and wrong-owner/denied/missing cases. Update legacy key derivation only where the test proves divergence; preserve enabled authorization and Bedrock transport. Run affected Go packages and normal required build/CI checks.

## 3. Extraction adoption and layout compatibility

- [x] 3.1 Extend Arcadia `classes/test_image_evidence.py` and `classes/test_statement.py` using source and page/crop URLs on different configured roots. Exercise all five existing image-review callers, public/private bucket provisioning settings, PNG/JPG originals, PDFs, native grants, rejected document scope and supported Bedrock paths; assert exact storage keys and provider inputs.
- [x] 3.2 Replace Arcadia's separate hostname, validator and path-conversion decisions with the released SDK resolver. Reuse its signature detector. Preserve current task/document checks, authorized originals, image selection/budget and external transport. Update the existing dependency declaration only after the human-owned SDK release.
- [x] 3.3 Extend ai-server `document/classes/test_file.py`, `document/test_util.py` and the maintained process-file reader test with the same configured alias shape. Keep the existing File implementation and old string-valued `uploadReplaceURL` behavior unless a failing production-reader case requires a minimal fix.
- [x] 3.4 Run existing extraction suites and maintained boundary replays for Arcadia legacy, Arcadia v1, generic v1 and ADP v1. Record transport evidence separately from extraction placement replays; do not update expected fixtures to hide changed output.

## 4. Helm configuration distribution

- [x] 4.1 Extend existing `src/groundx/tests/extract_test.yaml` and storage/file-access render coverage for alias distribution with the gateway on/off, both alias-empty and alias-present settings, S3/MinIO/S4 bucket roots and a distinct extraction store. Assert generated config contents and unchanged deployment resources when disabled.
- [x] 4.2 Add `groundx.file.urlAliases` to the existing file helper; render the shared aliases into layout `uploadReplaceURL` and extraction `url_aliases`. Emit the existing Go alias configuration even with `enabled: false`. Validate alias syntax independently of protected readiness. Exclude aliases for other storage identities.
- [x] 4.3 Render `url_aliases` only for nonempty aliases and extend the existing compatible-SDK guard for that case, so an older image cannot silently ignore configured aliases. Preserve old no-alias constructor rendering. Mirror changed templates into `helm/` and run `.build/bin/validate-helm.sh`; add no CI script/job.

## 5. Guidance and release handoff

- [x] 5.1 Update SDK CONTRIBUTING/Unreleased notes, Cashbot file-access guide, layout config guide, Helm operator guide and existing Harness architecture/on-prem/extraction references. Document exact settings, namespace/bucket-prefix mapping, persistence, native-grant rules and unchanged public API/MCP/generated-client contracts; synchronize derived Harness bundles normally.
- [x] 5.2 Prepare implementation PRs from their plan/work branches and include local-artifact cleanup and the release handoff. Preserve unrelated working trees. Record current CI and SDK regeneration protection; do not publish the SDK or pin arbitrary image versions. Keep the plan open until its release and acceptance tasks are settled, and archive in the implementation PR when complete.
- [x] 5.3 Inventory actual hosted runtime configuration resources read-only. Present sanitized exact alias configuration diffs and rollout/rollback commands before any saved config or deployment change. No SQL, IAM, bucket-policy, DNS or additional infrastructure change is planned.
- [x] 5.4 After compatible builds and separate deployment approval, test dev mixed-root public/protected PDFs, PNG/JPG, source/page/crop/X-Ray/extract links, SDK document/search readback, signed-link expiry and wrong-owner denial. Prove provider image inputs and expected synthetic extraction fields. Record model accuracy separately from transport success. Keep production unchanged until its exact rollout is approved; do not gate cloud on deferred live on-prem certification.
- [x] 5.5 Before producing raw local evidence, initialize and close the exact owning run root through the linked-repository artifact procedure. Clean synthetic resources, retain only bounded lifecycle results, and archive with implementation closeout. Do not create another bookkeeping PR solely to archive.

Implementation evidence and the human SDK release dependency are recorded in [implementation.md](implementation.md). SDK 4.1.6 is released, its extraction consumer is deployed, and the cloud acceptance record below completes the release handoff. Vendor-specific qualification remains deferred.

Local implementation artifacts are closed; see [local-artifact-closeout.md](local-artifact-closeout.md). Task 5.5 cleanup is complete. The remaining vendor-specific qualification belongs to the on-prem 0.2.9 plan.


## Closeout, 2026-10-29

Merged implementation and released SDK support are complete. Cashbot's archived `verify-cloud-file-access` production rollout records the exact builds and bounded public/protected PDF, PNG and JPG acceptance, legacy-link compatibility, policy precedence, sharing expiry and synthetic cleanup. It does not claim a full production ADP accuracy replay, live vendor qualification, installed MCP/delegated-client certification or named-customer sign-off.

Deferred release, backend qualification, unverified client/customer acceptance and any future infrastructure-state adoption are owned by [the existing on-prem 0.2.9 plan](https://github.com/eyelevelai/groundx-on-prem/pull/162). Transferred items were not marked passed. This archival changes documentation only; it deploys no services, changes no configuration and performs no SQL or infrastructure operations.
