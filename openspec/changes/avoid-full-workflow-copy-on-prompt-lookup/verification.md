# Local verification

SDK source is based on pushed `main` commit `340b61e9e08e0ee04984385b4ed791b643d42965`. The singular-lookup test failed before the code change because a nested field read copied the parent group. It passes after the change and checks copy isolation, a nested path, and a missing field.

- `PYTHONPATH=src pytest -q --disable-warnings --maxfail=1`: 624 passed, 5 skipped, 68 subtests passed.
- Focused `mypy --follow-imports=silent` on changed SDK source and test: no issues. A type check that follows imports reports three existing errors in untouched `src/groundx/core/pydantic_utilities.py` and `src/groundx/extract/services/status.py`; no errors in changed files.
- `ruff check` on changed files, `poetry build`, the line-ending check, `git diff --check`, and strict OpenSpec validation passed. `ruff format --check` would reformat the existing manager file on the pushed base as well, so the unrelated formatting was preserved.
- Arcadia's full local suite against this SDK source: 1,359 passed, 27 skipped, 1 deselected, 78 subtests passed. This includes the promoted Arcadia legacy, Arcadia v1, generic v1, and ADP v4 compact replay. Arcadia Pyright and line-ending checks passed.

This is local source-level evidence, not an installed-package release or live extraction. The private Nitel 1,909-charge boundary was not available in either working tree for a fresh replay. The exact-boundary timing and output-parity check remain open. SDK release, Arcadia dependency bump, and deployment remain outside this review change.

An instrumented protected ADP v4 replay found a separate Arcadia statement path that explicitly requests whole SDK maps 5,016 times. The SDK singular-accessor fix does not change those explicit whole-map getters. A timed replay measured 8.39 seconds in the two whole-map getters during a 36.64-second run. This is a separate performance opportunity, not evidence that the statement path caused the Nitel charge delay or a gate for this SDK change.
