# line-ending-policy Specification

## Purpose
TBD - created by archiving change age-212-standardize-line-ending-policy. Update Purpose after archive.
## Requirements
### Requirement: Tracked source files are normalized to LF
Root `.gitattributes` SHALL normalize tracked Python, Markdown, JSON, YAML, TOML, and config/
dotfile source to LF line endings in Git, tailored to the extensions actually tracked in this
repo (`.py`, `.md`, `.json`, `.yml`/`.yaml`, `.toml`, dotfiles).

#### Scenario: Text source file is checked out
- **WHEN** a tracked `.py`, `.md`, `.json`, `.yml`/`.yaml`, or `.toml` file is checked out or
  committed on any platform
- **THEN** Git normalizes its line endings to LF per `.gitattributes`

### Requirement: Known binary formats are excluded from normalization
`.gitattributes` SHALL mark `poetry.lock` and `.DS_Store` (the binary/lock formats actually
tracked in this repo) as `binary`, so Git never applies line-ending normalization to them.

#### Scenario: Binary-marked file is checked out
- **WHEN** `poetry.lock` or a tracked `.DS_Store` file is checked out or diffed
- **THEN** Git treats it as binary and does not rewrite its line endings or attempt a text diff

#### Scenario: No Windows command-file carve-out needed today
- **WHEN** the repo's tracked files are inventoried (`git ls-files`)
- **THEN** no `.bat`/`.cmd` files are present, so `.gitattributes` needs no CRLF carve-out for
  them today, and the policy documents the pattern (`*.bat text eol=crlf`) for future additions
  without adding an unused rule

### Requirement: Editors default to LF for source and docs
Root `.editorconfig` SHALL set `end_of_line = lf`, UTF-8 charset, and `insert_final_newline =
true` as the default for source, documentation, and config files.

#### Scenario: Editor opens a tracked source file
- **WHEN** a contributor's `.editorconfig`-aware editor opens a `.py`, `.md`, `.json`, `.yml`/
  `.yaml`, or `.toml` file in this repo
- **THEN** the editor defaults new content in that file to LF line endings, UTF-8 encoding, and
  a trailing newline

### Requirement: Guard script fails when tracked files contain CRLF or mixed line endings
`scripts/check-line-endings.sh` SHALL scan tracked text files and exit non-zero with a clear
list of offending file paths when any contain CRLF (`\r\n`) or mixed line endings. Binary-marked
paths (`poetry.lock`, `.DS_Store`) are excluded from the scan. **Polarity: finalize failure** —
the guard must not report success when an offender exists.

#### Scenario: A tracked text file contains CRLF line endings
- **WHEN** `scripts/check-line-endings.sh --all` runs against a tracked working tree that
  contains a `.py` or `.md` file with CRLF line endings
- **THEN** the script exits non-zero and prints that file's path in its offender list
- **AND** the script does NOT exit 0 or omit the file from the offender list (finalize-failure
  polarity: a CRLF offender must never be silently treated as passing)

#### Scenario: A tracked text file has mixed LF and CRLF line endings
- **WHEN** `scripts/check-line-endings.sh --all` runs against a working tree containing a
  tracked file with both LF and CRLF line endings present
- **THEN** the script exits non-zero and lists that file as an offender

### Requirement: Guard script passes cleanly on a fully LF-normalized repo
`scripts/check-line-endings.sh --all` SHALL exit 0 and print no offenders when every scanned
tracked text file uses LF line endings. **Polarity: finalize success** — a clean repo must not
be reported as failing.

#### Scenario: Full scan of an LF-only working tree
- **WHEN** `scripts/check-line-endings.sh --all` runs against a working tree where every tracked
  text file (excluding binary-marked paths) uses LF line endings
- **THEN** the script exits 0 and reports zero offenders
- **AND** the script does NOT exit non-zero or flag any file (finalize-success polarity: a clean
  scan must never be reported as a failure)

### Requirement: `--all` mode scans every tracked file, not just changed files
`scripts/check-line-endings.sh` SHALL support an `--all` flag that scans every currently tracked
text file (via `git ls-files`), independent of any diff/changed-file set. This repo's CI invokes
`--all` because the confirmed baseline has zero existing offenders, so no changed-files
workaround is needed.

#### Scenario: `--all` flag is passed
- **WHEN** `scripts/check-line-endings.sh --all` is invoked
- **THEN** the script enumerates every tracked text file in the repository (excluding
  binary-marked paths) and checks each one for CRLF/mixed line endings, regardless of whether it
  changed in the current branch

### Requirement: The guard runs in a separate CI workflow from the generated `ci.yml`
A new GitHub Actions workflow at `.github/workflows/line-endings.yml` SHALL run
`scripts/check-line-endings.sh --all` on `push` and `pull_request`. The Fern-generated
`.github/workflows/ci.yml` SHALL NOT be modified.

#### Scenario: A pull request is opened or updated
- **WHEN** a pull request is opened against this repo or a push lands on any branch
- **THEN** `.github/workflows/line-endings.yml` runs `scripts/check-line-endings.sh --all` and
  the job fails if the script exits non-zero

#### Scenario: `ci.yml` is unaffected
- **WHEN** the line-ending guard workflow is added
- **THEN** `.github/workflows/ci.yml` remains byte-identical to its pre-change content (no
  edits), so the next Fern regeneration is unaffected by this change

### Requirement: Guard-related files survive Fern regeneration
`.fernignore` SHALL list `.gitattributes`, `.editorconfig`, `scripts/check-line-endings.sh`, and
`.github/workflows/line-endings.yml`, so a future `fern generate` run does not remove or
overwrite them.

#### Scenario: Fern regenerates the SDK
- **WHEN** `fern generate` runs against this repo after this change lands
- **THEN** `.gitattributes`, `.editorconfig`, `scripts/check-line-endings.sh`, and
  `.github/workflows/line-endings.yml` are left untouched because each path is listed in
  `.fernignore`

### Requirement: The guard command is discoverable from `AGENTS.md`
`AGENTS.md` SHALL include an entry pointing contributors to the line-ending guard so it is
discoverable from the repo's existing table-of-contents entrypoint (`.fernignore`-protected, so
the entry survives Fern regeneration).

#### Scenario: A contributor is about to commit line-ending-sensitive changes
- **WHEN** a contributor reads `AGENTS.md` looking for validation commands to run before
  committing
- **THEN** they find a row pointing them to `scripts/check-line-endings.sh` as the line-ending
  guard command

