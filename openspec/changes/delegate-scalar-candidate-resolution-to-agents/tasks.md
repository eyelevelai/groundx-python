# Tasks

## 0. Establish pushed baselines

- [ ] 0.1 Create the SDK implementation branch from the then-current pushed
  `groundx-python` `origin/main`. Verify the reviewed candidate symbols and
  tests still match this plan before editing.
- [ ] 0.2 Base Internal Arcadia consumer work on the pushed branch containing
  merged PR 102, not an unrelated local checkout. Record the exact SDK and
  Internal Arcadia source commits.
- [ ] 0.3 Confirm `src/groundx/extract/`, `tests/extract/`, and `openspec/` remain
  protected by `.fernignore`. Do not edit generated Fern code.
- [ ] 0.4 Reconcile this plan with active `normalize-extracted-value-types` work.
  Keep type coercion there and candidate preservation here. Prove confidence is
  metadata only when both changes are installed together.

## 1. Lock the SDK candidate contract with failing tests

- [ ] 1.1 Replace the test that requires higher-ranked candidates to clear
  lower-ranked alternatives with tests proving the first observed candidate
  remains selected and every later unique candidate remains available.
- [ ] 1.2 Add table-driven string identity tests for outer-whitespace trimming,
  case-insensitive comparison, preserved first casing, and significant internal
  whitespace.
- [ ] 1.3 Add exact type-sensitive identity tests for null, booleans, integers,
  floats, lists, mappings, and nested JSON values. Prove `true`, `1`, and `1.0`
  remain distinct.
- [ ] 1.4 Add extracted-field envelope tests proving identity uses the inner
  value, the first envelope is retained, and different confidence values do not
  affect selection, ordering, or dedupe.
- [ ] 1.5 Add presence tests proving a missing key creates no candidate while an
  explicit null, empty string, or empty list does. Prove repeated-row empty
  handling is unchanged.
- [ ] 1.6 Add duplicate-observation tests proving all unique source pages merge
  in first-seen order for the selected candidate and every alternative.
- [ ] 1.7 Add public contract tests proving dataclass fields and imports remain
  unchanged, `selected` is first observed, `alternatives` retain all later
  unique values, and provisional `final_output` matches `selected`.
- [ ] 1.8 Run the focused SDK tests and confirm they fail for the current
  ranking, empty-value filtering, and alternative-clearing behavior.

## 2. Implement transport-only SDK candidate collection

- [ ] 2.1 Remove scalar candidate quality, hardcoded default-value ranking,
  source-page ranking, confidence ranking, and higher-ranked replacement from
  `src/groundx/extract/custom_outputs.py`.
- [ ] 2.2 Add one private candidate-identity helper implementing only the
  approved string and exact JSON equality rules. Keep confidence and other
  envelope metadata outside the identity decision.
- [ ] 2.3 Make singular route loading presence-aware so explicit null, empty
  string, and empty list reach candidate collection while missing keys do not.
  Keep repeated route behavior unchanged.
- [ ] 2.4 Keep the first unique candidate as selected and provisional
  `final_output`. Append all later unique candidates without semantic ranking.
- [ ] 2.5 Merge all unique source pages for duplicate observations without
  replacing the retained value or envelope.
- [ ] 2.6 Audit the full SDK custom-output reassembly path for confidence-based
  candidate branching. Remove any such branch and add a regression for each
  removed decision.
- [ ] 2.7 Update SDK docstrings and readback documentation so `selected` and
  `final_output` are described as provisional when alternatives exist.
- [ ] 2.8 Run focused custom-output and route-reassembly tests until green.

## 3. Build and prove an exact SDK candidate wheel

- [ ] 3.1 Run changed-file Ruff checks and formatting checks, focused extraction
  tests, the full hand-written extraction test suite, Mypy, line-ending checks,
  and `git diff --check`.
- [ ] 3.2 Build one candidate wheel without publishing it. Record source commit,
  filename, and SHA-256.
- [ ] 3.3 Install the exact wheel into an isolated Internal Arcadia environment
  based on the pushed PR 102 branch and verify the installed wheel hash.

## 4. Lock the Internal Arcadia consumer contract with failing tests

- [ ] 4.1 Add SDK handoff tests proving every candidate and all page numbers
  survive `_sdk_scalar_candidate_sets`, Celery serialization, statement branch
  copies, reconcile, QA, and save diagnostics.
- [ ] 4.2 Add prompt snapshot tests proving each conflicted field renders an
  ordered candidate object array with `value`, complete `source_pages`, and
  exact `provided_pages`.
- [ ] 4.3 Add reconcile-trigger tests for default-like and empty candidates.
  Prove two unique candidates always invoke reconcile and one unique candidate
  does not.
- [ ] 4.4 Add image-selection tests proving canonical page dedupe, one available
  page per candidate first, round-robin fill, complete source-page metadata,
  and a hard maximum of 30 attached images.
- [ ] 4.5 Add a failure test for more than 30 candidates requiring distinct
  images. Assert no model call occurs and the error names the field, candidate
  count, and limit.
- [ ] 4.6 Add reconcile-application tests proving an existing or novel returned
  value becomes current, the provisional value remains in candidate history,
  pending conflicts clear only after valid application, and no source page is
  invented for an agent-created value.
- [ ] 4.7 Add QA tests proving candidate history survives unchanged and a novel
  QA value is appended without invented source pages.
- [ ] 4.8 Add a trace test proving exact prompt, candidate mapping, attached
  image count, source page count, agent response, current value, and candidate
  history can be reconstructed without exposing candidate history in customer
  JSON.
- [ ] 4.9 Run the focused tests and confirm they fail for the current plain value
  array, first-page-only evidence selection, and history-clearing behavior.

## 5. Implement agent-owned reconciliation in Internal Arcadia

- [ ] 5.1 Keep `_routed_final_candidate_evidence` as durable runtime candidate
  history and `_routed_final_conflicts` as pending reconciliation state. Do not
  use one structure for both meanings.
- [ ] 5.2 Build reconciliation fields directly from complete candidate history.
  Trigger on more than one unique candidate without semantic or confidence
  filtering.
- [ ] 5.3 Render each candidate with `value`, `source_pages`, and
  `provided_pages`. Update the reconcile prompt to explain that only provided
  pages are visible. Keep the existing plain JSON response shape.
- [ ] 5.4 Replace first-page-only selection with candidate-first, round-robin
  page selection. Deduplicate actual images and retain every source-page number
  in prompt metadata.
- [ ] 5.5 Reuse PR 102 field batching. Keep the existing 30-image maximum. Fail
  one oversized field before the model call rather than adding multi-pass
  orchestration or silently hiding evidence.
- [ ] 5.6 Apply a valid reconcile response through one helper that sets the
  current routed value, preserves all prior candidates, appends a novel agent
  value with `origin: reconcile_agent`, and clears only pending conflict state.
- [ ] 5.7 Reuse the same evidence-preservation helper for QA updates, using
  `origin: qa_agent` for novel values.
- [ ] 5.8 Preserve candidate history across `to_celery`, `from_celery`, branch
  merges, save, and authorized diagnostic traces. Do not add it to customer
  final JSON.
- [ ] 5.9 Audit statement candidate, reconcile, QA, image, and save code for
  confidence-based decisions. Confidence may be copied as metadata but must not
  affect any branch.

## 6. Verify the coordinated behavior

- [ ] 6.1 Run focused Internal Arcadia statement, reconcile prompt, image
  selection, serialization, route merge, save, and trace tests against the exact
  candidate wheel.
- [ ] 6.2 Run the full Internal Arcadia unit suite, Pyright checks, line-ending
  checks, and `git diff --check`.
- [ ] 6.3 Run protected offline regressions for the current reproduction,
  Arcadia legacy, Arcadia v1, generic v1, and ADP. Name the exact test or fixture
  and result for every surface.
- [ ] 6.4 Add a targeted regression using the known default-like conflicts that
  motivated this change. Prove reconcile is called, receives both values and
  their evidence, and its selected value reaches final output.
- [ ] 6.5 Prove the 30-image request contains no duplicate page images, records
  total document pages, total candidate source pages, attached page count, and
  the exact page numbers attached.
- [ ] 6.6 Strictly validate this producer OpenSpec change and any consumer
  tracking plan created during implementation. Confirm no customer documents,
  X-Rays, prompts, responses, credentials, or local run artifacts are
  committed.

## 7. Release, pin, and deploy reversibly

- [ ] 7.1 Merge the SDK PR only after the exact candidate wheel passes the
  consumer gates. Give the human Fern release owner the requested next version,
  merged commit, wheel hash, validation evidence, semantic compatibility note,
  and Internal Arcadia pin requirement. Do not publish from this repo.
- [ ] 7.2 Pin the released SDK version in Internal Arcadia and reinstall from
  the package index. Repeat focused, full-suite, protected-case, type,
  line-ending, and container checks from a clean environment.
- [ ] 7.3 Merge and deploy Internal Arcadia. Record the new and prior image
  identities before rollout.
- [ ] 7.4 Rerun the ADP side-by-side extraction and capture exact reconcile and
  QA requests, responses, candidate mappings, total document pages, candidate
  source pages, attached pages, and final field values.
- [ ] 7.5 Roll Internal Arcadia back to the prior image and SDK pin if the
  current reproduction or any protected surface regresses. No data rollback is
  required.

## 8. Close evidence safely

- [ ] 8.1 Store run evidence only under the approved ignored private artifact
  root with owner, reason, expiry, and source hashes.
- [ ] 8.2 Settle evidence as accepted, rejected, or superseded. Remove local raw
  prompts, responses, images, X-Rays, and customer files after disposition.
- [ ] 8.3 Archive this change only after the SDK release, Internal Arcadia pin
  and deployment, protected certification, ADP rerun, and evidence cleanup are
  complete.
