# Tasks

## 1. Contract Review

- [x] Confirm cashbot-go server-side validation semantics before finalizing SDK
      shape-validation behavior; the SDK stays compatible with the server-side
      downgrade guard but is not the authoritative update guard.
- [x] Re-read `groundx.extract` YAML preparation, `ExtractionDefinition`,
      create/update helpers, and error response classes.
- [x] Confirm which files are protected by `.fernignore` before editing.
- [x] Confirm the callback error body expected by cashbot-go
      `DocumentLayoutWebhook`.

## 2. Shape Validation Tests

- [x] Add fixtures for pure legacy, current v1, persisted workflow extract,
      execution-only workflow extract, and mixed invalid payloads.
- [x] Add tests proving pure legacy YAML remains accepted.
- [x] Add tests proving metadata without `extraction_policy_version: v1` fails
      clearly.
- [x] Add tests proving workflow-extract mappings require explicit
      `mapping_kind="workflow_extract"` where authored mapping ambiguity exists.

## 3. Create/Update Safety Tests

- [x] Add sync and async create helper tests for legacy and v1 definitions.
- [x] Add tests proving pure legacy updates are not rejected solely because the
      helper lacks existing-workflow context.
- [x] Add tests proving update helpers do not perform a default
      `workflows.get(...)` preflight read solely to enforce downgrade safety.
- [x] Add tests proving this change does not introduce an
      `allow_legacy_downgrade` option or any other implicit client-side
      downgrade guard without an explicit future context design.

## 4. Implement

- [x] Keep this phase behind the Arcadia terminalization fix and cashbot-go
      server-side validation; do not add SDK behavior that becomes required for
      files to terminalize.
- [x] Add the smallest shape-classification helper needed by the tests.
- [x] Wire classification into loader and create/update helper validation.
- [x] Do not add a legacy-downgrade opt-in, existing-workflow context argument,
      or default update-time preflight read in the SDK as part of this change.
- [x] Verify or extend the extraction error response helper for raw fatal-task
      callback bodies.
- [x] Update SDK docs/docstrings for accepted shapes, invalid mixed shapes, and
      the fact that downgrade protection is enforced server-side in this phase.

## 5. Verify

- [x] Run targeted extraction helper and prompt-manager tests.
- [x] Run `poetry run pytest -rP tests/custom tests/extract`.
- [x] Run `poetry run mypy .`.
- [x] Run `OPENSPEC_TELEMETRY=0 npx -y @fission-ai/openspec@1.3.1 validate harden-extraction-workflow-contract-validation --strict`.
