## 1. Policy files (non-behavioral)

- [x] 1.1 Add root `.gitattributes` normalizing `*.py`, `*.md`, `*.json`, `*.yml`, `*.yaml`,
  `*.toml`, and common dotfiles to LF; mark `poetry.lock` and `*.DS_Store` `binary`; add a
  commented-out `*.bat`/`*.cmd` CRLF pattern for future additions (none tracked today).
  `TDD N/A: static Git config file, not executable behavior.`
- [x] 1.2 Add root `.editorconfig` defaulting `end_of_line = lf`, `charset = utf-8`,
  `insert_final_newline = true` for source/docs/config file globs.
  `TDD N/A: static editor-defaults file, not executable behavior.`

## 2. Guard script (verified inline, no committed test file)

- [x] 2.1 Implement `scripts/check-line-endings.sh`: enumerate tracked files via `git ls-files`,
  support `--all` (full scan) and a default changed-vs-base-ref scan, exclude binary-marked
  paths, flag any file containing a `\r` byte, print the offender list, exit non-zero if any
  offenders found else exit 0.
  `TDD N/A (matches sibling repos in this rollout): verified inline during apply per 2.2–2.4,
  not via a committed test file.`
- [x] 2.2 RED (inline, scratch fixture): create a temporary file outside any binary/excepted
  path containing CRLF line endings, run `scripts/check-line-endings.sh --all` against the
  working tree, and confirm it reports that file as an offender and exits non-zero
  (finalize-failure polarity — must fail, not silently pass).
- [x] 2.3 GREEN: remove the scratch CRLF fixture, re-run `scripts/check-line-endings.sh --all`
  against the (clean, tracked-only) working tree, and confirm it exits 0 with no offenders
  reported (finalize-success polarity).
- [x] 2.4 Confirm the scratch fixture from 2.2 was fully removed (`git status` clean) — nothing
  about this verification is committed, no new test file is added under `tests/`.

## 3. CI wiring

- [x] 3.1 Add `.github/workflows/line-endings.yml` — new, separate workflow running
  `scripts/check-line-endings.sh --all` on `push` and `pull_request`. Do NOT modify
  `.github/workflows/ci.yml` (Fern-generated).
  `TDD N/A: CI workflow config, verified by the CI run itself, not a unit test.`

## 4. Fern-regeneration safety (required)

- [x] 4.1 Update `.fernignore` to add all four new paths: `.gitattributes`, `.editorconfig`,
  `scripts/check-line-endings.sh`, `.github/workflows/line-endings.yml` — so the next `fern
  generate` does not clobber them.
  `TDD N/A: static config-file edit.`

## 5. Documentation

- [x] 5.1 Add a row to `AGENTS.md`'s `Topic | Read when` table pointing to
  `scripts/check-line-endings.sh` as the line-ending guard command (per plan-gate correction:
  `AGENTS.md`, not `CONTRIBUTING.md`, since `.fernignore` protects the former, not the latter).
  `TDD N/A: documentation edit.`

## 6. Local validation (record output for handoff)

- [x] 6.1 Run `scripts/check-line-endings.sh --all` locally against this repo's current tracked
  tree and record the output (expect: 0 offenders, matching the confirmed baseline).
- [x] 6.2 Run `git diff --check` after all policy-file changes and confirm it reports no
  whitespace/line-ending errors.
- [x] 6.3 Run `poetry run mypy .` and `poetry run pytest -rP -n auto .` and confirm both pass.

Cross-repo coordination and deferred items (other repos' offender cleanup, per-repo guard
rollout order, follow-up tickets for repos needing a separate normalization PR) are tracked in
the workspace-level `openspec/changes/AGE-212-standardize-line-ending-policy/tasks.md`, not
duplicated here.
