# Implementation and release handoff

Configured alternate file roots now identify the same storage bucket in Go,
Python extraction and generated Helm configuration. Stored links are unchanged.
Public and protected references retain their existing authorization checks.
Native signed links retain their exact HTTP request and cannot fall back to
service credentials after failure.

## Source changes

| Repository | Change |
| --- | --- |
| groundx-python | Optional `ContainerUploadSettings.url_aliases`, shared `Upload.storage_key`, and adoption by `DocumentRequest.load_images`. Exact native URI keys survive S3, MinIO and S4 adapters. |
| cashbot-go | Shared `config.Upload.FileRoots` used by existing resolvers, URL utilities and image readers. Primary aliases remain attached to their storage identity. |
| internal-arcadia-agents | Existing image validation, native reads and Bedrock conversion reuse the SDK resolver and signature detector. Task/document checks and image selection remain intact. |
| groundx-on-prem | Existing `fileAccess.trustedOrigins` reaches Go, layout and extraction with the gateway enabled or disabled. Separate extraction stores do not inherit primary-store aliases. |
| ai-server | Existing reader behavior is retained and covered by extended alias/key/denial tests. The configuration guide describes the same operator mapping. |
| groundx-studio-harness | Existing architecture, on-prem and SDK/extraction references describe configuration and release order. Derived bundles are synchronized; plugin patch version is 2.6.30. |

Existing test files were extended. No CI jobs, generated SDK files, public API
contracts, database objects, IAM permissions or deployment resources were added.
The adapter change removes only an explicit native URI prefix; legacy bare-key
parsing is retained.

## Local evidence

| Surface | Result |
| --- | --- |
| Python SDK | 834 tests passed, 2 skipped, 106 subtests passed, including optional aiohttp coverage. Mypy passed all 286 source/test files; touched-file Ruff and wheel/sdist builds passed. |
| Extraction runtime | 1,740 tests passed, 1 deselected, 180 subtests passed with the local SDK source. Full Pyright: no errors; four optional IPython-source warnings. |
| Protected extraction cases | Maintained compact replay passed for Arcadia legacy, Arcadia v1, generic v1 and ADP v1. Captured fixtures and expected outputs were not changed. |
| Image preparation | Mixed current/alias PDF and PNG/JPG sources, both provisioning settings, supported review callers and Bedrock paths retain exact storage keys and provider image bytes. Native grants, wrong-document references, denied reads and external HTTP paths remain covered. |
| Go | Config, utility, fileaccess, prompt and ratelimit short suites and race suites passed. Partner file-access/source readback passed after rebase onto current master `6b5a066a`. Affected-package builds, vet and LF checks passed. |
| Layout | 18 existing File, utility and process-file reader tests passed. |
| Helm | Full gate passed: 545 tests and 850 unchanged snapshots, both chart trees, template mirrors and Minikube render. Generated extraction settings refuse an SDK lacking alias support. |
| Harness | Full validation, extraction gate, 26/26 chart-grounded on-prem checks, mirror and version-bump checks passed. |

The full Go summarizer short suite also passed after two malformed test fixture
joins were changed to the existing `utility.FileURL` helper. Their previous
host and path concatenation omitted `/`; the production layout and processed-file
writers already insert it. Existing comparator and error assertions remain
unchanged. No malformed-host acceptance was added to production readers.

The exact-key adapter test failed five of nine cases before its fix, then passed
all nine through production image loading and S3/MinIO/S4 adapters. Only native
storage clients were replaced with recording byte stores. These are local
contract tests, not live vendor certification or model-accuracy measurements.

Arcadia's separate Redis/Celery gate did not pass locally. On macOS the default
spawn worker cannot register dynamically defined test tasks. Using Linux-style
fork allowed five tests to pass, then the queue-admission test failed with a
worker shutdown timeout; the remaining integration cases were stopped. No
callback/queue source was changed. The normal Linux CI gate must pass after the
released SDK dependency is updated; the local extraction suite does not replace it.

The old workflow-placement handoff script expects removed Go fixture paths and
cannot run against the current source tree. Maintained compact replays provide
the four required placement checks instead. Plain Go `build ./...` still needs
entrypoint version generation and encounters two pre-existing command packages
without `main`; affected packages build successfully.

## Release order

1. Merge the SDK change. The human Fern release owner publishes Python SDK
   4.1.6 through the existing release workflow. Package metadata is unchanged in
   this implementation branch.
2. Update Arcadia's existing `groundx` requirement to that released version,
   rerun its normal CI and build the extraction image. Its implementation uses
   the local SDK source for current validation and is not ready to deploy with
   the currently declared 4.1.4 requirement.
3. Build Cashbot and adopt compatible extraction images before applying
   alias-bearing Helm or hosted runtime configuration. The chart's compatibility
   check intentionally refuses an old SDK when aliases are configured.
4. Inventory actual hosted configuration resources read-only, then show exact
   sanitized changes and rollback commands before changing saved configuration.
   Run dev public/protected extraction and all returned-link checks before a
   separately approved production rollout.

No cloud configuration, infrastructure, database, storage policy, release or
deployment was changed. Live cloud acceptance, container smoke with the released
SDK and live on-prem vendor certification remain separate gates. The plan stays
open until its release and acceptance tasks are settled.

## Pull requests

| Repository | PR | Release dependency |
| --- | --- | --- |
| groundx-python | [#116](https://github.com/eyelevelai/groundx-python/pull/116) | Merge before the human-owned SDK 4.1.6 release. |
| cashbot-go | [#1886](https://github.com/EyeLevel-ai/cashbot-go/pull/1886) | Independent Go build; coordinated configuration rollout follows validation. |
| internal-arcadia-agents | [#215](https://github.com/eyelevelai/internal-arcadia-agents/pull/215) | Draft until SDK 4.1.6 is published, the requirement is updated and normal Linux CI passes. Current CI fails because 4.1.4 lacks `storage_key`. |
| groundx-on-prem | [#162](https://github.com/eyelevelai/groundx-on-prem/pull/162) | Compatible extraction images before alias-bearing configuration. |
| ai-server | [#86](https://github.com/EyeLevel-ai/ai-server/pull/86) | Documentation and regression coverage only; no reader image change. |
| groundx-studio-harness | [#293](https://github.com/EyeLevel-ai/groundx-studio-harness/pull/293) | Guidance release 2.6.30; runtime compatibility remains explicit. |

All six PR heads match their pushed branch and local implementation commit.
Source worktrees remain for these unmerged PRs. Test dependencies and raw local
logs are governed by the implementation run's closeout receipt.
