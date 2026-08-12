## 0. Establish The Pushed Baseline

- [x] 0.1 Create the SDK change branch from the current pushed `origin/main`,
  carry this OpenSpec change onto it without unrelated local files, and verify
  the reviewed SDK symbols and Fern boundaries still match before implementation.

## 1. Lock The Shared Coercion Contract

- [x] 1.1 Add `CoercionResult` and `coerce_value` import expectations to
  `tests/extract/utility/test_utility.py`, then add a table-driven failing test
  for `str`, `int`, `float`, `list`, `dict`, unions, null, unknown targets, and
  impossible conversions. Assert value, exact Python type, matched status,
  converted status, and warning contents.
- [x] 1.2 Add explicit regressions for `True` to `"true"`, `False` to `"false"`,
  boolean to numeric unmatched null, `"0"` remaining a string, list and dict JSON
  encoding, JSON container parsing, decimal union selection, impossible
  conversion to null, direct null input, decimal-to-int truncation, and
  empty numeric text becoming null rather than zero. For every declared type,
  prove a missing or unmatched field remains present as null instead of becoming
  an empty string, list, or dict.
- [x] 1.2a Add a large integer-text regression proving integer coercion does not
  lose precision through a binary floating-point conversion.
- [x] 1.3 Run
  `poetry run pytest -q tests/extract/utility/test_utility.py` and confirm the
  tests fail because the shared interface does not exist.

## 2. Implement One SDK Conversion Boundary

- [x] 2.1 Implement `CoercionResult` and `coerce_value` in
  `src/groundx/extract/utility/utility.py` using exact type checks, JSON encoding
  and decoding, guarded numeric casts, deterministic union precedence, and
  unmatched null fallback.
- [x] 2.2 Export the new interface from
  `src/groundx/extract/utility/__init__.py`. Rewrite
  `coerce_numeric_string` as a compatibility wrapper that returns
  `coerce_value(...).value` without changing its signature or implementing a
  second conversion matrix.
- [x] 2.3 Add failing tests in `tests/extract/classes/test_prompt.py` proving a
  boolean does not pass direct integer or float validation. Add failing tests in
  `tests/extract/classes/test_field.py` proving all supported targets use the
  shared helper, date normalization remains unchanged, `True` for `str` reads as
  `"true"`, and missing or impossible values remain nonfatal nulls through
  readback and serialization for every declared type.
- [x] 2.4 Update `src/groundx/extract/classes/prompt.py` to validate exact types.
  Update `src/groundx/extract/classes/field.py` to accept JSON-compatible input,
  delegate primitive conversion, make `none_value` return `None` for every
  declared type, preserve date handling, and expose the latest content-free
  warning without serializing it into extracted JSON.
- [x] 2.5 Route SDK confidence validation through `coerce_value`. Preserve its
  public tuple shape, return a field-scoped nonfatal warning for unmatched input,
  and never include the raw value in the warning.
- [x] 2.6 Run
  `poetry run pytest -q tests/extract/utility/test_utility.py tests/extract/classes/test_prompt.py tests/extract/classes/test_field.py`
  and confirm all focused conversion tests pass.

## 3. Make Parser Retry Output-Safe

- [x] 3.1 Add failing tests under `tests/extract/agents/` proving malformed JSON
  recovery makes two provider calls, returns the corrected result, preserves
  exact trace events, and writes no raw response or stack trace to stdout,
  stderr, or ordinary logs.
- [x] 3.2 Add wrong-native-type and wrong-parsed-type regressions for
  `process_response`, `AgentTool`, and the shared behavior used by `AgentCode`.
  Include native and JSON-string `answer.type` envelopes whose outer object is
  valid but whose unwrapped value has the wrong type. Prove the first failure
  consumes the configured parser retry, exhaustion remains terminal, and the
  exception message contains expected-type context without raw provider content.
- [x] 3.3 Remove direct parser-retry output, `traceback.print_stack()`, and raw
  provider content from raised parser exception messages in
  `src/groundx/extract/agents/agent.py`. Unwrap supported response envelopes
  before validating the final value against `expected_types`. Keep the exception
  class and expected-type context. Keep any retry log content-free and debug-only,
  and preserve the existing `AgentTool` trace events.
- [x] 3.4 Add transport-failure and post-parser `TypeError` tests proving parser
  retry does not consume or replace another retry owner's failure.
- [x] 3.5 Run `poetry run pytest -q tests/extract/agents` and confirm the focused
  parser suite passes with captured stdout, stderr, and logs empty of provider
  content.

## 4. Prove SDK Compatibility Before Release

- [x] 4.1 Inventory every SDK caller of `coerce_numeric_string`,
  `Prompt.valid_value`, `ExtractedField.set_value`, `ExtractedField.get_value`,
  and `process_response`. Add a focused regression for each distinct supported
  call shape not covered above.
- [x] 4.2 Confirm every modified source and test path is protected by the current
  `.fernignore`. Do not edit generated files or package metadata.
- [ ] 4.3 Run `poetry run ruff check .`, `poetry run ruff format --check .`,
  `poetry run mypy .`, `poetry run pytest -rP -n auto .`,
  `scripts/check-line-endings.sh --all`, and `git diff --check`.
  Changed files pass Ruff. The repository-wide Ruff check still reports 29
  pre-existing import-order and f-string findings outside this change. Mypy,
  parallel pytest, line endings, and diff checks pass.
- [x] 4.4 Build one candidate wheel with `poetry build`. Record its SHA-256 and
  source commit. Do not release it.
  Candidate: `groundx-3.9.2-py3-none-any.whl`, source commit
  `d37d8d7679ca29a3c03dea1460016d9a82b2b55f`, SHA-256
  `76d71b1bb1f00404a3243424df16eccc0926a00bc9d4ee962c83986cdb47abc2`.

## 5. Prove The Internal Arcadia Consumer

- [ ] 5.1 In an isolated Internal Arcadia environment, install the exact wheel
  from task 4.4 and verify its SHA-256. Do not update `requirements.txt` to an
  unreleased version.
- [ ] 5.2 Inventory every Internal Arcadia caller of
  `coerce_numeric_string`, `Prompt.valid_value`, and `ExtractedField`. Keep those
  callers on the compatibility wrapper unless the caller writes model output to
  a typed field and needs match metadata. Classify each migrated caller as a new
  field write or an update to existing state.
- [ ] 5.3 Add regressions for the current reproduction and the AGE-272 field
  shape with native booleans for `employer_match_true_up` and
  `safe_harbor_annual_true_up`. Assert lowercase strings, preserved sibling
  fields, no new conversion log, and successful document completion. Do not
  claim this reproduces the original terminal cause.
- [ ] 5.4 Replace `_json_string_field_value` and other local primitive conversion
  code only where shared-helper tests prove equivalent or corrected behavior.
  Migrate only model-output field-writing boundaries that need match metadata to
  `coerce_value`; keep other callers on the compatibility wrapper. Keep
  prompt-specific business rules separate and add no second conversion helper.
- [ ] 5.5 At each migrated field-writing boundary, write null when an unmatched
  result creates a field with no valid prior value. When reconcile, QA, or
  another update targets an existing valid field, reject the unmatched update
  and preserve the prior value. Add the content-free metadata to one
  request-local stage aggregate. Extend one existing stage completion or
  terminal record with document, task, stage, workflow group, count, field
  names, source types, and target types. Include no raw value, prompt, response,
  source URL, credential, or exception message.
- [ ] 5.6 Add statement, meter, charge, and confidence regressions for every
  distinct migrated write shape. Prove new unmatched fields serialize as null,
  unmatched updates do not erase valid prior values, sibling fields continue,
  and only one stage aggregate is produced.
- [ ] 5.7 Run the focused Internal Arcadia conversion, statement, meter, charge,
  parser-retry, logging, and callback tests named by
  `age-272-retry-terminal-agent-diagnostics` against the exact candidate wheel.

## 6. Update Harness Guidance

- [ ] 6.1 In `groundx-studio-harness`, update
  `skills/groundx-extraction-workflows/references/2_schema_design.md`,
  `16_prompt_writing.md`, and `prompt-quality.md` with the shared conversion
  contract and explicit-prompt guidance.
- [ ] 6.2 Update retrieval evals for boolean string output, container JSON text,
  unmatched null behavior, and parser retry diagnostics.
- [ ] 6.3 Run `node scripts/sync-plugin.mjs`,
  `node scripts/sync-plugin.mjs --check`, and `node scripts/validate.mjs`. Do not
  hand-edit generated plugin mirrors.

## 7. Release And Roll Out Once

- [ ] 7.1 Run focused offline regressions against the candidate wheel for the
  current reproduction, Arcadia legacy, Arcadia v1, generic v1, and ADP v1.
  Record the exact test or fixture and result for each surface.
- [ ] 7.2 Merge the tested SDK PR. Give the human Fern release owner the requested
  next version, merged commit, wheel hash, validation evidence, and Internal
  Arcadia consumer pin. Do not tag, dispatch, or publish from GroundX Python.
- [ ] 7.3 Pin the released version once in Internal Arcadia, reinstall from the
  package index, and repeat focused, full-suite, type, line-ending, container,
  and protected-surface checks.
- [ ] 7.4 Complete the terminal diagnostic storage and rollout tasks in
  `age-272-retry-terminal-agent-diagnostics`. Record the new and prior Internal
  Arcadia image identities before deployment.
- [ ] 7.5 Rerun document `5e68599a-e879-452b-a29e-753d3336fbce` with workflow
  `1e066a84-1afe-4477-9c9c-82cd67ec9806` when an authorized production rerun is
  available. Confirm completion and lowercase strings. Record this as current
  behavior, not proof of the missing original terminal cause.
- [ ] 7.6 Roll Internal Arcadia back to the recorded image if the current
  reproduction or any protected surface regresses. Preserve rejected-run
  evidence until disposition.

## 8. Close Evidence Safely

- [ ] 8.1 Before certification writes output, create one ignored dedicated run
  root under `groundx-python/openspec/work/normalize-extracted-value-types/` with
  owner, reason, and expiry. Use the installed Harness linked-repository local
  artifact procedure, not Harness root-locked helpers.
- [ ] 8.2 Settle the run as accepted, rejected, or superseded. Preserve only
  approved sanitized handoffs, remove the exact run root, and verify its absence
  before archive.
- [ ] 8.3 Strictly validate this OpenSpec change and the linked Internal Arcadia
  change with OpenSpec 1.3.1. Run `git diff --check` and confirm neither change
  contains customer documents, X-Rays, prompts, model output, credentials, or
  local run artifacts.
