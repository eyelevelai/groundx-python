# Tasks: Extraction Pseudo Group Operational Closeout

## Completed Plan Archives

- [x] Archive SDK implementation plan:
      `openspec/changes/archive/2026-06-03-extract-yaml-group-fragments/`
- [x] Archive Fern docs implementation plan:
      `/Users/benjaminfletcher/git/eyelevel-fern-config/openspec/changes/archive/2026-06-03-document-extraction-workflow-walkthrough/`
- [x] Archive harness implementation plan:
      `/Users/benjaminfletcher/git/groundx-studio-harness/openspec/changes/archive/2026-06-03-extraction-yaml-fragments-and-howto/`
- [x] Archive Arcadia reassembly-helper implementation plan:
      `/Users/benjaminfletcher/git/internal-arcadia-agents/openspec/changes/archive/2026-06-03-extraction-pseudo-groups-reassembly/`

## SDK Release And Generated-Source Durability

- [x] Confirm the first `groundx[extract]` package version that includes
      `FinalFieldPath`, `PreparedExtractionYaml`, and `prepare_extraction_yaml`
      exported from `groundx.extract`.
- [x] If the released version is not `3.5.8`, update the harness requirement in
      `/Users/benjaminfletcher/git/groundx-studio-harness/skills/groundx-extraction-workflows/templates/requirements.txt`
      and rerun the harness validation plan.
- [x] Trace Fern generation for `groundx-python` and confirm
      `src/groundx/extract/**` and `tests/extract/**` are protected source files
      or intentionally regenerated from a source of truth.
- [x] If regeneration overwrites the extract SDK work, move the behavior into
      the true generated source, `.fernignore` only the minimum hand-written
      surface, or update the Fern config so the generated output preserves the
      extract extension.
- [x] Add a packaging smoke test in the release workflow or local release
      checklist that imports:
      `from groundx.extract import FinalFieldPath, PreparedExtractionYaml, prepare_extraction_yaml`.

## Granular Hardening

- [x] Record SDK hardening coverage already present in
      `tests/extract/prompt/test_manager.py`: legacy identity route maps,
      top-level duplicate YAML key rejection, duplicate pseudo routes, unknown
      final paths, malformed JSON Pointer paths, `_defs` field composition,
      unsupported `_defs` prompt text, unsupported pseudo-group metadata,
      empty pseudo-group fields, YAML merge key rejection, cyclic YAML rejection,
      slot positive inheritance/override cases, ambiguous multi-parent slot
      inheritance, and partially missing slot inheritance.
- [x] Move the remaining explicit SDK fixtures that are not yet covered as
      named regression tests: malformed pseudo field mapping, pseudo/final group
      name collision, pseudo-group `include`, scalar prompt shorthand rejection,
      duplicate keys inside nested field prompt mappings, duplicate
      `_pseudo_groups` names, duplicate pseudo field keys, duplicate `_defs`
      fragment names, duplicate final field names where not already covered,
      `slot: null` inheritance behavior, and empty-string slot preservation.
- [x] Confirm harness-specific fixture follow-up is tracked in
      `/Users/benjaminfletcher/git/groundx-studio-harness/openspec/changes/extraction-pseudo-group-release-hardening/tasks.md`.

Note: keep these as hardening tests only unless they expose a real behavior gap;
real behavior gaps require a focused fix plus adversarial review.

## Lint And Local Hygiene

- [x] Decide whether broad Ruff cleanup in `src/groundx/extract` and
      `tests/extract` is worth doing in the generated repo. If yes, create a
      separate lint-only change so style churn does not mix with feature work.
- [x] Resolve untracked `.cgcignore` files in
      `/Users/benjaminfletcher/git/eyelevel-fern-config`,
      `/Users/benjaminfletcher/git/groundx-studio-harness`, and
      `/Users/benjaminfletcher/git/internal-arcadia-agents`: commit them only if
      they are intentional repo policy; otherwise remove them from the working
      trees.

## Cross-Repo Release Gate

- [x] Confirm the Arcadia runtime wiring plan remains open as the owning plan.
- [x] Confirm the public docs publish/preview plan remains open as the owning
      plan.
- [x] Confirm the harness release hardening plan remains open as the owning
      plan.
- [x] Run the SDK gates:
      `poetry run pytest -q .`,
      `poetry run mypy .`,
      `poetry run pyright -p pyrightconfig.json`.
- [x] Run the Pylance parity gate from the local workspace:
      `npx -y pyright@latest -p /Users/benjaminfletcher/git/extract-sdk/pyrightconfig.json`.
- [x] Run `git diff --check` in all four repos.
- [x] Record final release-readiness evidence in this plan before archiving it.

### Validation Evidence 2026-06-03

- `poetry run pytest -q .`: 142 passed, 2 skipped, 5 subtests passed.
- `poetry run mypy .`: success, no issues found in 202 source files.
- `poetry run pyright -p pyrightconfig.json`: 0 errors, 0 warnings.
- `npx -y pyright@latest -p /Users/benjaminfletcher/git/extract-sdk/pyrightconfig.json`:
  0 errors, 0 warnings.
- `git diff --check`: passed in `groundx-python`, `eyelevel-fern-config`,
  `groundx-studio-harness`, and `internal-arcadia-agents`.
- Removed untracked auto-generated CodeGraphContext `.cgcignore` files from
  `eyelevel-fern-config`, `groundx-studio-harness`,
  `groundx-studio-harness/plugins/groundx-studio-harness`, and
  `internal-arcadia-agents`.
- Broad Ruff cleanup is intentionally out of scope for this pseudo-group chain;
  create a separate lint-only change if style cleanup becomes valuable.
- Fern generation durability is satisfied for this change because
  `.fernignore` protects `src/groundx/extract`, `tests/extract`, and `openspec`
  from Fern regeneration. No source move is currently required.

### Validation Evidence 2026-06-04

- `groundx[extract]==3.5.9` is the first checked released package version that
  exports `FinalFieldPath`, `PreparedExtractionYaml`, and
  `prepare_extraction_yaml`.
- The harness requirement was initially updated to `groundx[extract]>=3.5.9` in
  `/Users/benjaminfletcher/git/groundx-studio-harness/skills/groundx-extraction-workflows/templates/requirements.txt`
  and both plugin mirrors; the requirement was later raised to
  `groundx[extract]>=3.6.0` after the public clean-import fix shipped.
- Added `openspec` to `.fernignore` after Fern release regeneration removed the
  SDK OpenSpec tree.
- Added local release-checklist coverage that installs `.[extract]` into a
  fresh virtual environment and imports:
  `from groundx.extract import FinalFieldPath, PreparedExtractionYaml, prepare_extraction_yaml`.
- Removed the runtime `pytest` import from `src/groundx/extract/agents/agent.py`
  so clean consumer installs do not rely on development-only dependencies.
- Verified the local patched package with:
  `python3 -m venv /tmp/groundx-clean-import-green && /tmp/groundx-clean-import-green/bin/python -m pip install '.[extract]' && /tmp/groundx-clean-import-green/bin/python -c 'from groundx.extract import FinalFieldPath, PreparedExtractionYaml, prepare_extraction_yaml'`.
- Historical blocker: the public `3.5.9` package still contained the pre-fix
  runtime import, so downstream harness/docs plans could not claim the
  clean-install gate was satisfied for public consumers.
- Final local SDK sweep:
  `git diff --check && poetry run pytest -q . && poetry run mypy . && poetry run pyright -p pyrightconfig.json`
  passed with 142 tests passed, 2 skipped, 5 subtests passed, mypy success in
  202 source files, and pyright 0 errors / 0 warnings.
- Final patched clean-install smoke passed with a fresh virtual environment
  installing local `.[extract]` and importing `FinalFieldPath`,
  `PreparedExtractionYaml`, and `prepare_extraction_yaml`.
- Historical blocker: public package smoke for `groundx[extract]==3.5.9`
  failed importing `groundx.extract` with
  `ModuleNotFoundError: No module named 'pytest'`, confirming that a follow-up
  SDK package release was required.
- CI follow-up bugfix 2026-06-04: after removing the runtime `pytest` import,
  CI still failed test collection without Pillow because `groundx.extract` and
  `groundx.extract.classes` eagerly imported optional image-dependent modules.
  Added lazy public export tables for both packages, changed `AgentCode` and
  `AgentTool` image annotations to type-checking-only Pillow imports, and added
  `tests/extract/test_import_boundaries.py` to prove non-image extract imports
  do not require Pillow.
- `poetry run pytest -q tests/extract/test_import_boundaries.py`: first failed
  on the eager `PIL.Image` import, then passed after the lazy import fix.
- `poetry run pytest -rP -n auto .`: passed with 143 tests passed and 2
  skipped after the Pillow import-boundary fix.
- CI follow-up bugfix 2026-06-04, part 2: CI next failed without Google client
  libraries because `groundx.extract.prompt` and `groundx.extract.services`
  package initializers eagerly imported `PromptManager`, `ObjectStore`, and
  `SheetsClient`. Made both package namespaces lazy and mapped top-level prompt
  exports directly to their defining modules.
- Extended `tests/extract/test_import_boundaries.py` to block `PIL`, `google`,
  `googleapiclient`, and `gspread`; it first failed on the eager
  `google.oauth2` import, then passed after the lazy prompt/services fix.
- Final local SDK sweep after the Google import-boundary fix:
  `git diff --check && poetry run pytest -rP -n auto . && poetry run mypy . && poetry run pyright -p pyrightconfig.json`
  passed with 143 tests passed, 2 skipped, mypy success in 203 source files,
  and pyright 0 errors / 0 warnings.
- Public SDK blocker closeout 2026-06-04: GitHub release workflows for
  `groundx-python` `3.6.0` completed successfully, PyPI reports `groundx`
  latest as `3.6.0`, and a fresh public install of `groundx[extract]==3.6.0`
  successfully imports `FinalFieldPath`, `PreparedExtractionYaml`, and
  `prepare_extraction_yaml`. The SDK package availability blocker is resolved;
  remaining release-readiness work is cross-repo runtime/docs/harness closeout.
- Final release-readiness remains open because Arcadia runtime wiring, docs
  preview/publish, and harness release hardening still have open plan items.
- Cleanup execution 2026-06-04:
  - SDK-only parser hardening was moved to
    `openspec/changes/extract-yaml-parser-hardening/`.
  - Harness release hardening remains owned by
    `/Users/benjaminfletcher/git/groundx-studio-harness/openspec/changes/extraction-pseudo-group-release-hardening/`.
  - Fern docs preview/publish remains owned by
    `/Users/benjaminfletcher/git/eyelevel-fern-config/openspec/changes/publish-extract-data-from-documents/`.
  - Arcadia runtime wiring remains owned by
    `/Users/benjaminfletcher/git/internal-arcadia-agents/openspec/changes/extraction-workflow-metadata-runtime-wiring/`.
  - This coordinator plan has no remaining unique open work and can be archived.
