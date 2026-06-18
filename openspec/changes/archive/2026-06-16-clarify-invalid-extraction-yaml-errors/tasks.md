# Clarify Invalid Extraction YAML Errors Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:test-driven-development` for each code task and `superpowers:verification-before-completion` before closeout. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make invalid extraction YAML fail with actionable errors while preserving `create_extraction_workflow(path=...)` for valid YAML.

**Architecture:** Keep all changes in the hand-written extract surfaces. `prepare_extraction_yaml(...)` owns structural YAML validation and message quality; workflow definition loaders and create/update helpers should preserve and add path/source context without replacing the root cause.

**Tech Stack:** Python, pytest, GroundX hand-written extract SDK, OpenSpec.

---

## Files

- Modify: `/Users/benjaminfletcher/git/groundx-python/src/groundx/extract/prompt/utility.py`
- Modify: `/Users/benjaminfletcher/git/groundx-python/src/groundx/extract/workflows.py`
- Test: `/Users/benjaminfletcher/git/groundx-python/tests/extract/prompt/test_manager.py`
- Test: `/Users/benjaminfletcher/git/groundx-python/tests/extract/test_extraction_workflow_definitions.py`
- Test: `/Users/benjaminfletcher/git/groundx-python/tests/custom/test_extraction_workflow_client_exports.py`

## Task 1: Add Failing Loader Error Tests

- [x] Add a regression where raw YAML starts with unsupported top-level scalar
      metadata:

  ```yaml
  unsupported_policy_version: v1
  statement:
    fields:
      account_number:
        prompt: Extract account number.
  ```

  Expected error: names `unsupported_policy_version`, explains that generic SDK
  top-level keys must be extraction groups, reserved keys, or supported SDK
  metadata keys, and tells advanced callers to register metadata keys or convert
  to supported workflow YAML.

- [x] Add a positive regression proving
      `extraction_policy_version: v1` succeeds as supported SDK metadata and is
      preserved in `PreparedExtractionYaml.top_level_metadata`.

- [x] Run:

  ```bash
  poetry run pytest tests/extract/prompt/test_manager.py -q
  ```

  Expected before implementation: the new negative test fails because the error
  is still low-level.

## Task 2: Improve Hand-Written Extract Loader Errors

- [x] Update `src/groundx/extract/prompt/utility.py` so top-level non-mapping
      keys that are not reserved keys, supported SDK metadata keys, or
      registered metadata keys fail with an actionable `ValueError`.

- [x] Keep nested mapping errors strict and preserve existing messages where
      they already identify the correct malformed nested path.

- [x] Run:

  ```bash
  poetry run pytest tests/extract/prompt/test_manager.py -q
  ```

  Expected: new loader error tests pass and existing prompt loader tests pass.

## Task 3: Preserve Error Context Through YAML Shortcut Helpers

- [x] Add regressions for sync
      `GroundX.create_extraction_workflow(path=..., name=...)` and
      `GroundX.update_extraction_workflow(id, path=..., name=...)` using an
      invalid YAML temp file.

- [x] Add sync regressions proving the same helpers accept
      `extraction_policy_version: v1` and preserve it in the workflow `extract`
      payload.

- [x] Add matching async regressions for
      `AsyncGroundX.create_extraction_workflow(path=..., name=...)` and
      `AsyncGroundX.update_extraction_workflow(id, path=..., name=...)` using an
      invalid YAML temp file.

- [x] Add async regressions proving the same helpers accept
      `extraction_policy_version: v1` and preserve it in the workflow `extract`
      payload.

- [x] Expected error: includes the YAML path or source context plus the
      actionable offending key message from the loader.

- [x] Update `src/groundx/extract/workflows.py` only as needed to preserve the
      root cause and add path/source context. No `src/groundx/ingest.py` change
      was required because those public helpers delegate to the shared workflow
      loader.

- [x] Run:

  ```bash
  poetry run pytest tests/extract/test_extraction_workflow_definitions.py tests/custom/test_extraction_workflow_client_exports.py -q
  ```

  Expected: YAML shortcut error tests pass and existing helper tests pass.

## Task 4: Final SDK Verification

- [x] Run:

  ```bash
  OPENSPEC_TELEMETRY=0 npx -y @fission-ai/openspec@1.3.1 validate clarify-invalid-extraction-yaml-errors --strict --json
  poetry run pytest tests/extract/prompt/test_manager.py tests/extract/test_extraction_workflow_definitions.py tests/custom/test_extraction_workflow_client_exports.py -q
  poetry run mypy .
  poetry run pytest -rP -n auto .
  git diff --check
  ```

- [x] Adversarially review that the SDK still promotes `path=` for valid YAML
      and only improves the invalid YAML failure mode.
