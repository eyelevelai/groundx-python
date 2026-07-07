# Harden Extraction Workflow Contract Validation Design

## Goals

- Preserve legacy YAML support in the SDK.
- Make v1 and workflow-extract payloads distinguishable by contract, not guess.
- Reject mixed or metadata-bearing payloads that are missing explicit v1 markers
  without adding client-side stored-state downgrade enforcement.
- Give Arcadia a verified SDK-compatible error callback body for fatal
  pre-hydration failures.

## Non-Goals

- No removal of legacy YAML.
- No harness support for authoring legacy YAML.
- No generated OpenAPI/Fern schema rename.
- No broad rewrite of extraction workflow helper APIs.

## Shape Classification

The SDK should expose or internally use one classifier before create/update:

| Shape | Accepted | Notes |
| --- | --- | --- |
| pure legacy authored YAML | yes | Top-level extraction groups only, such as `statement`, `meters`, and `charges`, with no v1 metadata. |
| v1 authored YAML | yes | Requires `extraction_policy_version: v1` when workflow metadata, pseudo groups, route metadata, or policy metadata are present. |
| persisted workflow extract | yes | Contains SDK persisted metadata such as `_groundx_persisted_extract`; loaded as workflow extract, not guessed from simple group keys. |
| execution-only workflow extract | yes with `mapping_kind="workflow_extract"` | Preserved exactly; authored inspection metadata may be unavailable. |
| mixed or stripped v1 | no | Metadata without marker, partial persisted metadata, field-level workflow routing keys in reserved metadata positions without v1 marker, or v1-looking payloads that lost required metadata. Ordinary legacy field names, prompt text, identifiers, and customer fields are not treated as v1 metadata merely because their strings match reserved words. |

The classifier can remain private if the public helper errors are clear and
well tested. If a public enum is introduced, it should be treated as a stable
hand-written SDK surface.

## Create/Update Validation

Workflow create helpers may accept pure legacy or v1 definitions. They should
reject only structurally invalid or mixed payloads.

Workflow update helpers validate only the supplied definition shape in this
change. They should not add a default SDK preflight `workflows.get(...)` call,
an `allow_legacy_downgrade` flag, or a new existing-workflow context surface.
Creating a new pure legacy workflow, updating with pure legacy input, and
loading execution-only workflow extracts all remain supported when the supplied
shape is structurally valid.

Server-side validation is the authoritative place to enforce v1-to-legacy
downgrade safety because cashbot-go can load the stored workflow during update.
If the SDK later adds client-side downgrade enforcement, that future change must
first define an explicit hand-written context surface and opt-in semantics. It
must not be inferred from `workflow_id` and must not perform hidden update-time
reads.

This SDK work is the final compatibility phase, after the Arcadia stuck-file
fix and cashbot-go server-side validation contract. It must not block the
production terminalization fix, and it must not add hidden update-time reads to
compensate for missing server-side state.

## Error Callback Helper

The SDK currently provides extraction task classes used by internal agents.
Before Arcadia implements raw-Celery fatal callback fallback, the SDK should
verify the error response body required by the GroundX callback handler. The
minimum callback body must include `documentID`, `taskID`, `code`, and
`message`. If the callback contract accepts model or processor identifiers, the
SDK helper should carry them as optional fields without making them required for
legacy callers.

## Test Strategy

Tests should cover each classifier row, sync and async create/update helpers,
and the no-hidden-preflight update contract. Fixtures should include:

- pure legacy utility-bill YAML;
- current v1 Arcadia YAML;
- persisted workflow extract from v1 YAML;
- execution-only workflow extract;
- metadata-without-marker invalid YAML;
- pure legacy update when existing workflow state is unavailable.
