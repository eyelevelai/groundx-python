# Tasks: Extract YAML Parser Hardening

## Fixture Audit

- [x] Compare each proposed fixture below against existing coverage in
      `tests/extract/prompt/test_manager.py` and delete any duplicate task
      before writing new tests.
- [x] Add a named regression test for malformed pseudo field mapping.
- [x] Add a named regression test for pseudo/final group name collision.
- [x] Add a named regression test for pseudo-group `include`.
- [x] Add a named regression test for scalar prompt shorthand rejection.
- [x] Add a named regression test for duplicate keys inside nested field prompt
      mappings.
- [x] Add a named regression test for duplicate `_pseudo_groups` names.
- [x] Add a named regression test for duplicate pseudo field keys.
- [x] Add a named regression test for duplicate `_defs` fragment names.
- [x] Add a named regression test for duplicate final field names where not
      already covered.
- [x] Add a named regression test for `slot: null` inheritance behavior.
- [x] Add a named regression test for empty-string slot preservation.

## Validation

- [x] Run `poetry run pytest -q tests/extract/prompt/test_manager.py`.
- [x] Run `poetry run pytest -q tests/extract/test_import_boundaries.py`.
- [x] Run `poetry run pytest -q .`.
- [x] Run `poetry run mypy .`.
- [x] Run `poetry run pyright -p pyrightconfig.json`.
- [x] Run `git diff --check`.

### Validation Evidence 2026-06-04

- `poetry run pytest -q tests/extract/prompt/test_manager.py`: 41 passed,
  5 subtests passed.
- `poetry run pytest -q tests/extract/test_import_boundaries.py`: 1 passed.
- `poetry run pytest -q .`: 154 passed, 2 skipped, 5 subtests passed.
- `poetry run mypy .`: success, no issues in 203 source files.
- `poetry run pyright -p pyrightconfig.json`: 0 errors, 0 warnings,
  0 informations.
- `npx -y @fission-ai/openspec@1.3.1 validate --all --json`: 1/1 valid.
- `git diff --check`: passed.
