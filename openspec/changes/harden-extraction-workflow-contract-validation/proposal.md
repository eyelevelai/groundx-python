# Change: Harden Extraction Workflow Contract Validation

## Why

The Python SDK is a shared boundary for harnesses, internal Arcadia agents, and
direct customer code. It must keep pure legacy extraction YAML valid, while also
rejecting mixed or metadata-bearing workflow `extract` payloads that are missing
an explicit v1 marker. Stateful downgrade protection remains a server-side
cashbot-go responsibility during workflow update, where stored workflow state is
available.

The recent Arcadia incident showed why shape ambiguity is dangerous: a
legacy-looking deployed workflow can be valid legacy, or it can be a v1 workflow
that lost the metadata needed for routing and agent selection. The SDK should
classify these shapes clearly and fail before API calls when the source is mixed
or ambiguous.

## What Changes

- Add explicit extraction workflow shape classification for authored YAML,
  persisted workflow extracts, execution-only workflow extracts, and invalid
  mixed payloads.
- Keep pure legacy YAML supported by `prepare_extraction_yaml(...)` and
  first-class create/update helpers.
- Require v1 authored metadata to be explicitly marked by
  `extraction_policy_version: v1`.
- Reject mixed metadata-without-marker shapes before workflow create/update.
- Keep workflow update helpers from adding hidden existing-workflow reads or
  client-side downgrade enforcement in this change; server-side cashbot-go
  validation remains authoritative for rejecting accidental v1-to-legacy
  downgrades when stored workflow state is available.
- Verify or extend the SDK extraction error response helper so Arcadia can build
  a valid callback body from raw fatal-task identifiers.

## Impact

- Public SDK remains backwards compatible for pure legacy YAML.
- Harness-authored workflows continue to use v1 only.
- Invalid mixed payloads fail earlier with clearer errors.
- Valid pure legacy payloads are not rejected because they lack harness/v1
  metadata.
- Any new error-response field must remain hand-written SDK code and must not
  require generated Fern schema renames.
