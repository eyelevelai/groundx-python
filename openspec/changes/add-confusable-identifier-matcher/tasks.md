## 1. Freeze Current Behavior

- [x] 1.1 Record the current GroundX Python ref, open PRs, and the exact
  identity and relationship callers in `custom_outputs.py`.
- [x] 1.2 Run focused and full test baselines and keep every existing test,
  fixture, expected output, and score unchanged.
- [x] 1.3 Add new failing tests for both public functions, every approved and
  rejected string case, nonstring helper rejection, and raw-value preservation.
- [x] 1.4 Add new failing production-entrypoint tests for repeated-record
  identity, advanced identity indexing, `exact_attrs` no-op behavior, populated
  relationship key shape, and stable parent selection.

## 2. Add The Shared Functions

- [x] 2.1 Add `src/groundx/extract/comparison.py` with string-only
  `match_key(value: str) -> str` and
  `values_match(left: str, right: str) -> bool`, explicit nonstring rejection,
  and no matching modes or external dependency.
- [x] 2.2 Export both functions from `groundx.extract` without changing
  generated top-level SDK files.
- [x] 2.3 Prove case folding, all `str.isspace()` characters, and only
  `{0, o}`, `{1, i, l}`, and `{8, b}` affect string comparison.
- [x] 2.4 Prove both helpers reject nonstrings and production callers invoke
  them only for strings.

## 3. Route SDK Matching Through The Functions

- [x] 3.1 Route every repeated-record identity string key in indexes,
  partitions, dedupe, thresholds, shortcuts, and direct comparisons through the
  shared functions while preserving existing typed wrappers.
- [x] 3.2 Route relationship string equality through `values_match` while
  preserving value unwrapping, absence rules, populated-key shape, and stable
  parent order.
- [x] 3.3 Remove the runtime effect of `identity_match.exact_attrs` while
  preserving metadata validation, preparation, persistence, and readback.
- [x] 3.4 Add narrow production-behavior checks that fail if repeated identity
  or relationship matching reintroduces a separate case, whitespace,
  confusable, or exact transform.

## 4. Verify And Release

- [x] 4.1 Run focused tests, the full pytest suite, mypy, changed-file Ruff,
  build, line-ending checks, and strict OpenSpec validation.
- [ ] 4.2 Exercise the Internal Arcadia consumer change against this branch and
  complete its protected-case and collision gates before publishing.
- [x] 4.3 If any existing evidence fails, stop before editing it and obtain human
  approval for the specific input and behavioral change.
- [ ] 4.4 Require the `eyelevel-fern-config`
  `document-universal-identifier-matching` public-docs change to merge before the
  SDK release.
- [ ] 4.5 After collision approval, merge the implementation and prepare the
  human release handoff with the merged commit, requested version, validation
  evidence, and Internal Arcadia as the downstream consumer.
