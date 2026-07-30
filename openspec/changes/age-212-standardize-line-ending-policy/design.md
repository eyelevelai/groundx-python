Confirmed baseline (per proposal.md): 0 existing CRLF/mixed-line-ending offenders across all
tracked files, so policy + guard land together with no separate normalization PR.

## Goals / Non-Goals

**Goals:**
- Every tracked source file normalizes to LF in Git, independent of contributor OS/editor.
- Binary formats actually tracked in this repo (`poetry.lock`, `.DS_Store`) are never
  line-normalized.
- A guard script + CI workflow fail fast on any future CRLF/mixed-line-ending regression,
  scanning the full tracked tree (`--all`) since there is no existing-offender backlog to work
  around.
- Guard-related files (`.gitattributes`, `.editorconfig`, `scripts/check-line-endings.sh`,
  `.github/workflows/line-endings.yml`) are fenced from Fern regeneration.
- The guard command is discoverable from `AGENTS.md`.

**Non-Goals:**
- No mechanical normalization PR — the 0-offender baseline means there is nothing to normalize.
- No `.bat`/`.cmd` CRLF carve-out — none are tracked today; the pattern is documented in
  `.gitattributes` as a comment for future additions, not encoded as an active rule.
- No change to `.github/workflows/ci.yml` — it is Fern-generated and regenerated on every `fern
  generate`; a change there would be silently discarded.
- No change to `src/groundx/` or any published API — this is repo tooling only (confirmed in
  proposal.md's Impact section).

## Decisions

### D1: `.fernignore` scope — hand-written layer only
This change's four new files live entirely outside Fern's generated surface. Per
`openspec/config.yaml` context, `.fernignore` currently fences `README.md`, `AGENTS.md`,
`src/groundx/ingest.py`, `src/groundx/csv_splitter.py`, `src/groundx/extract`, `tests/custom`,
`tests/extract`, `openspec`, and a handful of tooling dotfiles — `openspec/` is already fenced,
so this change's own artifacts survive regeneration without further action. The four *new* paths
this change adds (`.gitattributes`, `.editorconfig`, `scripts/check-line-endings.sh`,
`.github/workflows/line-endings.yml`) are not yet listed, so `.fernignore` must be updated to add
them — otherwise a future `fern generate` could remove or overwrite them. This is a required
task, not optional cleanup.

### D2: Separate CI workflow, not a `ci.yml` edit
`.github/workflows/ci.yml` is Fern-generated (matches Fern's Python-SDK CI template) and carries
no `.fernignore` entry today, so any hand-edit to it is discarded on the next regeneration. Rather
than fight that by fencing `ci.yml` itself (which would then also freeze it against legitimate
Fern-driven CI updates), this change adds a **new, independent** workflow file,
`.github/workflows/line-endings.yml`, fenced via `.fernignore` instead. Trade-off: two workflow
files instead of one extra job in the existing file — acceptable, since it keeps the
Fern-generated file untouched and regenerable at any time without re-litigating this guard.

### D3: Guard script supports `--all`; this repo's CI always passes `--all`
The guard script is written to support two modes: a default changed-files-only scan (useful for
a repo with a pre-existing offender backlog it hasn't cleaned up yet) and an explicit `--all`
flag that scans every currently tracked text file via `git ls-files`. Since this repo's confirmed
baseline is 0 offenders, `.github/workflows/line-endings.yml` invokes the script with `--all` —
there is no backlog to work around, so the full-repo scan is strictly stronger and catches a
regression anywhere in the tree, not only in files touched by the current PR.

### D4: Detection method — scan tracked files for `\r` bytes, skip binary-marked paths
The script enumerates tracked files with `git ls-files`, excludes paths Git already treats as
binary (`poetry.lock`, `.DS_Store` — matched against the same set `.gitattributes` marks
`binary`), and flags any remaining file containing a `\r` byte as an offender (covering both
pure-CRLF and mixed-LF/CRLF files). This needs no extra dependency beyond `grep`/`git`, matching
this repo's existing bias toward small, dependency-free shell tooling (`.fernignore` already
excludes `.vscode`, `.gitignore` similarly by plain pattern, not a helper library).

### D5: `.gitattributes` extension set — tailored to this repo's actual tracked files
Per the confirmed `git ls-files` extension inventory (251 `.py`, 74 `.md`, 41 `.json`, 2 `.yaml`,
1 `.yml`, 1 `.toml`, plus `poetry.lock` and one tracked `.DS_Store`), `.gitattributes` normalizes
`*.py`, `*.md`, `*.json`, `*.yml`, `*.yaml`, `*.toml`, and common dotfiles to LF, and marks
`poetry.lock` and `*.DS_Store` binary. No `*.bat`/`*.cmd` rule is added since none are tracked;
the CRLF-carve-out pattern is left as a documentation comment for future additions, per the
proposal's stated approach.

### D6: Guard-command doc line goes in `AGENTS.md`, not `CONTRIBUTING.md`
Per the plan-gate correction: `.fernignore` protects `AGENTS.md` (and `CLAUDE.md` redirects to
it) but does **not** protect `CONTRIBUTING.md` — an edit there is unfenced and outside what the
SDD pipeline's generation-safety guarantees cover. `AGENTS.md` is already this repo's
table-of-contents entrypoint (`Topic | Read when` rows), so the guard command is added as one
more row there rather than as new prose in `CONTRIBUTING.md`.

### No ADR
This is a small, reversible, single-repo tooling addition with no data-model, API, or
cross-service impact — it does not meet this repo's ADR bar (config.yaml: "Only required for
non-trivial additions; keep minimal otherwise").

## Risks / Trade-offs

- [Two CI workflow files instead of one] → Mitigation: each stays single-purpose;
  `line-endings.yml` is small and `.fernignore`-fenced, so it never conflicts with Fern-owned
  `ci.yml` changes.
- [Guard script's default (non-`--all`) mode is unused by this repo's own CI] → Mitigation:
  documented in D3 as intentional — the mode exists for parity with other repos in this
  cross-repo rollout that do have an offender backlog; this repo's confirmed 0-offender baseline
  means `--all` is the correct and sufficient invocation here.
- [Future contributor adds a `.bat`/`.cmd` file without updating `.gitattributes`] → Mitigation:
  the carve-out pattern is documented as a comment in `.gitattributes` so it's a one-line
  uncomment, not a rediscovery.
