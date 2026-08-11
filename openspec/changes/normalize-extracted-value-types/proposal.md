## Why

Structured extraction currently has two independently verified resilience gaps.

First, extracted-value conversion is split across `coerce_numeric_string`,
`Prompt.valid_value`, `ExtractedField`, and downstream consumers. The current SDK
can turn a native boolean for a string field into `"1.0"` or `"True"`, treats
booleans as numbers through Python subclassing, and does not provide one contract
for list and dict targets.

Second, the SDK owns response-parser retry but writes malformed provider content
and stack traces to ordinary process output. Internal Arcadia therefore disables
the parser retry and one malformed response can terminalize a document.

The original AGE-272 terminal `TypeError` cannot be assigned to either gap from
retained evidence. The cited production task later completed successfully and no
matching detailed terminal trace was retained. This change fixes the verified SDK
defects without treating either theory as the incident's proven root cause.

## What Changes

- Add one SDK coercion implementation for `str`, `int`, `float`, `list`, `dict`,
  declared type unions, and null.
- Convert compatible values deterministically. Native booleans become lowercase
  JSON text for string fields. A boolean supplied for a numeric field is
  unmatched and becomes null rather than plausible but incorrect numeric data.
- Return a type-safe null plus a content-free warning when conversion is
  impossible. Preserve that null through new field readback and serialization.
  When an unmatched model update targets a field that already has a valid
  value, keep the valid value instead of overwriting it with null. Do not pass
  the incompatible raw value to typed consumers.
- Route SDK field handling and confidence validation through the shared helper.
  Keep `coerce_numeric_string` only as a thin compatibility entry point over the
  same implementation so downstream callers do not fail on import.
- Remove direct parser-retry output, parser stack printing, and raw provider
  content from raised parser exception messages. Preserve exact parser evidence
  through the existing `AgentTool` trace callback.
- Validate the final value after the SDK unwraps an `answer.type` response.
  Wrong inner types therefore remain parser failures and consume the configured
  parser retry instead of escaping into later processing.
- Keep one SDK parser retry available to consumers. A parser failure remains
  terminal after configured retries are exhausted.
- Release the coercion and parser-output changes together, then let Internal
  Arcadia pin that one released version.
- Document the shared conversion contract and keep explicit output-shape prompts
  as the authoring default.

## Capabilities

### New Capabilities

- `extracted-value-coercion`: one non-failing SDK contract that converts
  extracted JSON values to declared schema types and reports unmatched values
  without failing a document.
- `agent-response-reliability`: parser retry writes no provider content or stack
  trace to ordinary output while exact evidence remains available through the
  trace callback.

### Modified Capabilities

(none)

## Impact

- **Hand-written SDK files:** `src/groundx/extract/utility/`,
  `src/groundx/extract/classes/field.py`,
  `src/groundx/extract/classes/prompt.py`, and
  `src/groundx/extract/agents/agent.py`. These paths are protected by
  `.fernignore`.
- **Public extract surface:** adds `CoercionResult` and `coerce_value`. The
  release owner chooses the next package version. This plan does not tag,
  dispatch, or publish a release.
- **Compatibility:** `coerce_numeric_string` keeps its call signature and
  primitive return shape. It delegates all conversion to `coerce_value`; there
  is no second conversion matrix. The wrapper prevents import failures in the
  SDK, Internal Arcadia, and legacy Arcadia, whose `groundx[extract]>=3.4.1`
  dependency can take a newer minor release automatically. Corrected values can
  differ from current behavior, including `True` becoming `"true"` rather than
  `"1.0"` or `"True"`, `"0"` remaining a string for a `str` target, and missing
  or unmatched values remaining null instead of becoming empty containers or
  strings.
- **Downstream consumer:** Internal Arcadia uses `coerce_value` only at
  model-output field-writing boundaries that need match metadata. Other callers
  remain on the compatibility wrapper. It removes only local conversion code
  duplicated by the SDK. New unmatched fields serialize as null. Unmatched
  reconcile or QA updates preserve an existing valid value. Internal Arcadia
  pins the one released SDK version, enables one parser retry, and owns terminal
  trace retention and service logging.
- **Consolidated extraction plan:** remaining cross-repo certification work is
  tracked in
  `internal-arcadia-agents/openspec/changes/complete-extraction-boundary-regression-coverage/tasks.md`.
- **Logging:** the SDK adds no ordinary log record for conversion or parser
  retry. A consumer may write one content-free retry decision record with its
  document and stage context. An impossible conversion is aggregated by a
  field-aware consumer, not logged independently by the SDK helper.
- **No API schema, database, workflow-data, or generated Fern change is
  required.**
- **Open design questions:** none.
