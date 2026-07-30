## Why

GitHub renders line-ending-only normalization (LF vs CRLF) as whole-file add/delete diffs, which
makes real review harder (see ai-server PR #41: a 1-line functional change to `detect_ocr.py`
rendered as 106 additions / 106 deletions). `groundx-python` has no explicit line-ending policy
today — no `.gitattributes`, no `.editorconfig`, and no CI/validation guard — so nothing stops a
future PR from reintroducing that class of noise. A scan of all tracked files in this repo found
**0 existing CRLF/mixed-line-ending offenders**, so the policy and guard can land together without
a separate mechanical normalization PR.

## What Changes

- Add root `.gitattributes` — normalize tracked source (`.py`, `.md`, `.json`, `.yml`/`.yaml`,
  `.toml`, config/dotfiles) to LF in Git; mark known binary formats (`.DS_Store`, `poetry.lock`)
  binary so they are never line-normalized. No `.bat`/`.cmd` files are currently tracked in this
  repo, so no CRLF carve-out is needed, but the pattern is documented for future additions.
- Add root `.editorconfig` — defaults editors to LF, UTF-8, and trailing-newline for source/docs/
  config files.
- Add `scripts/check-line-endings.sh` — a guard script that scans tracked text files for CRLF or
  mixed line endings and fails with a clear list of offenders; supports an `--all` mode (scan
  every tracked file) since this repo has zero existing offenders to work around.
- Add a **new, separate** GitHub Actions workflow `.github/workflows/line-endings.yml` that runs
  the guard script on push/PR. `.github/workflows/ci.yml` is **not modified** — it matches Fern's
  generated SDK CI template and is regenerated on every Fern run; a change there would be
  silently discarded.
- **Modify `.fernignore`** to add `.gitattributes`, `.editorconfig`, `scripts/check-line-endings.sh`,
  and `.github/workflows/line-endings.yml` — without this, the next Fern regeneration would
  overwrite/remove these hand-authored guard files. (`.fernignore` itself, `openspec/`, and
  `CONTRIBUTING.md` are already fenced or otherwise unaffected by Fern regen.)
- Document the guard command in `CONTRIBUTING.md`, alongside the existing `poetry run pytest` /
  `ruff` / `mypy` commands, per this repo's existing documentation convention.

No functional / API-surface changes. No changes to any file outside the hand-written /
`.fernignore`-protected layer.

## Capabilities

### New Capabilities
- `line-ending-policy`: repo-tailored `.gitattributes` + `.editorconfig` policy plus a CI-wired
  guard script that fails when tracked text files contain CRLF or mixed line endings, run
  separately from the Fern-generated `ci.yml`.

### Modified Capabilities
(none — no existing spec's requirements change)

## Impact

- **Affected files (all within the hand-written / `.fernignore`-protected layer):**
  - `.gitattributes` (new, root)
  - `.editorconfig` (new, root)
  - `scripts/check-line-endings.sh` (new)
  - `.github/workflows/line-endings.yml` (new — separate from the generated `ci.yml`)
  - `.fernignore` (modified — adds the 4 paths above)
  - `CONTRIBUTING.md` (modified — documents the guard command)
- **Public package surface (PyPI `groundx`):** unaffected. No semver impact — this is repo
  tooling/contribution hygiene only, not a change to `src/groundx/` or any published API.
- **Downstream consumers** (`internal-arcadia-agents`, `groundx-studio-harness`,
  `groundx-agent-harness`, `groundx-on-prem`): none affected — nothing in the installed package
  changes.
- **Fern regeneration:** confirmed the 4 new/changed guard-related paths must be (and will be)
  added to `.fernignore` so a future `fern generate` does not clobber them. `ci.yml` stays
  untouched and fully Fern-owned.
- **Existing offenders:** 0 found in a full repo scan (`git ls-files` + line-ending inspection) —
  no separate mechanical normalization PR is needed for this repo; policy + guard land together.
- **Open design questions:** none.
