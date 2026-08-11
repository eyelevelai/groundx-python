## Context

GroundX Python 3.9.2 has two separate SDK-owned problems.

`coerce_numeric_string`, `Prompt.valid_value`, and `ExtractedField` apply
different type rules. Python booleans pass some integer checks, so a boolean for
a string field can become `"1.0"` or `"True"`. List and dict handling is partly
implemented in downstream consumers instead of one SDK boundary.

The SDK also owns response parsing and configured parser retry. `AgentTool`
prints the malformed response before a retry, and `process_response` prints a
stack for wrong native or parsed types. Enabling retry unchanged would place
customer-derived output in container logs.

AGE-272 reported a terminal `TypeError` and inferred a boolean-to-string
mismatch from X-Ray output. The cited task and document later completed, and the
retained production logs do not contain the original terminal detail. A separate
governed ADP fixture proves malformed JSON can recover on a second parser
attempt, but it is not proof of AGE-272's exact cause. The implementation and
ticket must keep that distinction.

## Goals

- Make the SDK the only owner of primitive extracted-value coercion.
- Support every declared extraction type currently recognized by the SDK.
- Prevent one incompatible field value from failing a document.
- Keep typed outputs type-safe when conversion is impossible.
- Preserve null for missing and newly created unmatched fields instead of
  substituting an empty string, list, or dict. Preserve an existing valid value
  when a later reconcile or QA update is unmatched.
- Make configured parser retry safe to enable in containerized consumers.
- Ship both SDK changes in one tested release.

## Non-Goals

- No claim that either verified SDK defect caused the original AGE-272 failure.
- No new schema type such as `bool`.
- No prompt, workflow-routing, generated Fern, API, or database change.
- No broad rewrite of Internal Arcadia conversion call sites.
- No model-client, transport, Celery, or stage-retry policy change.
- No ordinary SDK log record for successful conversion or recovered parser retry.

## Shared Coercion Interface

Add these hand-written types under `groundx.extract.utility`:

```python
@dataclass(frozen=True)
class CoercionResult:
    value: typing.Any
    matched: bool
    converted: bool
    warning: typing.Optional[str] = None


def coerce_value(
    value: typing.Any,
    expected_types: typing.Optional[typing.Union[str, typing.List[str]]] = None,
) -> CoercionResult:
    ...
```

`coerce_value` is total for JSON-compatible inputs. It catches parse and cast
errors. An impossible or unknown target returns `value=None`, `matched=False`,
and a content-free warning containing source and target type names. The helper
does not log because it does not have document, stage, or field context.

`coerce_numeric_string` remains a compatibility entry point:

```python
def coerce_numeric_string(value, et=None):
    return coerce_value(value, et).value
```

This is one conversion implementation with two return shapes. Existing callers
receive only the selected primitive value. Field-aware code uses
`CoercionResult` when it needs match status or a warning. The old name remains
because it is exported by the SDK and is used by Internal Arcadia and legacy
Arcadia. Legacy Arcadia declares `groundx[extract]>=3.4.1`, so removing the name
could break it on an automatic minor upgrade.

## Conversion Rules

1. Return `None` unchanged with matched status.
2. Resolve declared type names. Unknown names return an unmatched null result.
3. Preserve an exact allowed Python type. Exact checks use `type(value)`, so a
   boolean does not masquerade as an integer.
4. For `int` and `float` unions, inspect numeric text and choose integer or float
   without losing decimals.
5. Attempt target conversions in declared order.
6. Return an unmatched null result when every supported conversion fails.

| Target | Accepted conversion |
| --- | --- |
| `str` | JSON scalar text for bool and numbers; compact JSON text for list and dict |
| `int` | int, float, numeric text parsed without a binary-float round trip; decimal truncation remains toward zero |
| `float` | int, float, numeric text |
| `list` | list unchanged; JSON array text parsed |
| `dict` | dict unchanged; JSON object text parsed |

The helper does not invent container shapes. It does not wrap scalars in lists,
convert dicts to lists, or create `{"value": ...}` wrappers. The exact string
`"0"` remains `"0"` for a string target. Empty text for a numeric target is
unmatched and becomes null; it is not converted to zero. A boolean for an `int`
or `float` target is also unmatched and becomes null. Treating `true` as one or
`false` as zero would turn a model type error into plausible wrong data.

## SDK Integration

- `Prompt.valid_value` uses exact-type validation. Conversion happens before
  validation.
- `ExtractedField.set_value` and `get_value` delegate primitive conversion to
  `coerce_value`. Existing date normalization remains separate.
- `ExtractedField.none_value` returns `None` for every declared type. Missing and
  unmatched fields therefore serialize as null, not as an empty string, list,
  or dict, and the field remains present.
- The field value annotation accepts JSON-compatible inputs before conversion.
- SDK confidence validation delegates to `coerce_value`, keeps its existing
  public tuple shape, and returns a field-scoped nonfatal warning for an
  unmatched value.
- `coerce_numeric_string` remains the compatibility path for existing consumers.
- Utility exports expose `CoercionResult` and `coerce_value`.

An unmatched raw value remains available to the caller that supplied it and to
authorized diagnostic capture. The typed extracted output contains null for the
field, not the raw value or an empty substitute. Sibling fields continue
processing. `coerce_value` does not decide update semantics. A consumer creating
a field uses the returned null. A consumer updating an existing field rejects an
unmatched update and keeps the prior valid value.

## Parser Retry Output Safety

Keep the existing `process_response` and `AgentTool.process` ownership:

- unwrap supported `answer.type` response envelopes before final type
  validation, then validate that final value against `expected_types`;
- remove `traceback.print_stack()` from wrong native and parsed type failures;
- remove direct stdout output before `AgentTool` retry;
- keep the terminal exception class and expected-type context, but remove the
  raw provider response from its message;
- keep any SDK retry log content-free and debug-only;
- preserve exact prompt, raw response, parsed response, parse error, and attempt
  events through the existing `AgentTool` trace callback;
- keep retry exhaustion terminal.

This plan does not add another parser or retry loop. Internal Arcadia can set
`response_parse_max_retries=1` after it pins the released SDK.

## Internal Arcadia Integration

Internal Arcadia consumes the release through its separate
`age-272-retry-terminal-agent-diagnostics` change:

- pin the one released SDK version containing both changes;
- use `coerce_value` directly at model-output field-writing boundaries that must
  preserve unmatched fields and collect match metadata;
- write null for an unmatched field only when no valid prior field exists;
- reject an unmatched reconcile or QA update when the target already has a
  valid value, preserving that value while recording the unmatched metadata;
- leave rendering, CSV, and other compatibility callers that do not need match
  metadata on `coerce_numeric_string`;
- remove only `_json_string_field_value` and other local conversion code proven
  equivalent to `coerce_value`;
- do not add an Internal Arcadia conversion helper or second conversion matrix;
- add no log for a successful conversion;
- aggregate unmatched fields into the existing stage completion or terminal
  record, with count, field names, source types, and target types, and without
  raw values or exception messages;
- preserve existing transport, stage-owned, model-client, Celery, and callback
  behavior.

Every direct caller of `coerce_numeric_string`, `Prompt.valid_value`, and
`ExtractedField` must be inventoried and tested before changing the shared
wrapper because the wrapper changes all of them at once. Only field-writing
callers that need `matched`, `converted`, or `warning` migrate to `coerce_value`.

## Harness Documentation

Update the root extraction references, then regenerate plugin mirrors. Document:

- all declared types use shared best-effort coercion;
- boolean string fields become lowercase `"true"` or `"false"`;
- container-to-string conversion uses JSON;
- impossible conversion yields a type-safe null for a new field, preserves a
  valid prior value on update, and produces one field-aware warning;
- explicit output-shape prompts remain preferred because coercion is a safety
  net.

## Release And Rollout

1. Build one SDK candidate wheel containing coercion and parser-output safety.
2. Install that exact wheel in an isolated Internal Arcadia environment.
3. Test the wrapper call inventory, field-aware integration, one parser retry,
   terminal callback behavior, and all protected extraction paths.
4. Merge the SDK PR and hand the tested commit, candidate evidence, requested
   next version, and Internal Arcadia consumer pin to the human Fern release
   owner. Do not tag, dispatch, or publish from this repo.
5. Pin the released version in Internal Arcadia and repeat consumer and
   container tests from a clean install.
6. Update Harness source references and regenerate both plugin bundles.
7. Deploy Internal Arcadia only after its terminal diagnostic storage gate is
   satisfied. Record the new and prior image identities for rollback.

If the protected current reproduction, Arcadia legacy, Arcadia v1, generic v1,
or ADP v1 regresses, roll Internal Arcadia back to the recorded image. The
additive SDK release remains available, but consumers need not adopt it until
their tests pass.

## Verification

- SDK coercion tests cover each scalar, container, union, null, unknown target,
  and impossible pair, including exact result types and warnings.
- SDK field tests prove `True` with `type: str` reads as `"true"` and an
  impossible conversion becomes a nonfatal null.
- SDK agent tests prove recovery and exhaustion retain trace events while
  stdout, stderr, and ordinary logs contain no stack or raw provider content.
- SDK agent tests cover native and JSON-string response envelopes whose outer
  object is valid but whose unwrapped `answer.type` has the wrong type. The
  first failure consumes one parser retry and the second remains terminal.
- Internal Arcadia tests cover every existing wrapper call shape, each migrated
  field-writing boundary, new-field null behavior, prior-value preservation,
  one stage-level warning aggregate, the AGE-272 field shape, parser recovery
  and exhaustion, and callback compatibility.
- Certification names evidence for the current reproduction, Arcadia legacy,
  Arcadia v1, generic v1, and ADP v1.
- Harness validation proves root references and generated bundles remain
  synchronized.

Any certification output follows the linked-repository manual artifact
procedure because this change is owned by `groundx-python`, not GroundX Studio
Harness. Raw X-Rays, prompts, model output, logs, and customer data remain
ignored and are removed after disposition.

## No ADR

This is a narrow hand-written extract utility and parser-output change. It adds
no service, storage, generated API, or deployment boundary.
