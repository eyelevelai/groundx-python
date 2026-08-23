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
- [ ] 1.5a Add requiredness tests proving a sole explicit null remains candidate
  evidence but does not satisfy a required route. Prove a required-field
  diagnostic is emitted independently of candidate count, while empty string,
  `false`, `0`, and empty list are not rejected by generic truthiness.
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
  Track required-route satisfaction separately so a sole null still emits the
  existing required-field diagnostic. Keep repeated route behavior unchanged.
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

## 3. Build and prove an SDK source candidate

- [ ] 3.0 Complete and validate Tasks 1 and 2 in
  `complete-scalar-candidate-provenance` on top of this change. Record the one
  combined SDK commit. Do not build or certify an earlier wheel.
- [ ] 3.1 Run changed-file Ruff checks and formatting checks, focused extraction
  tests from both SDK changes, the full hand-written extraction test suite,
  Mypy, line-ending checks, and `git diff --check`.
- [ ] 3.2 Build one candidate wheel on Python 3.11 without publishing it. Keep
  the repository's generated package version unchanged. Build only from the
  combined commit recorded in 3.0. Record source commit, filename, and SHA-256.
- [ ] 3.3 Install that source candidate into isolated Internal Arcadia and
  Studio Harness environments based on their required pushed refs. Verify the
  installed candidate hash in both environments.

## 4. Hand off Internal Arcadia implementation to its owning plan

- [ ] 4.1 Record the pushed `complete-scalar-reconcile-disposition` branch and
  commit used for consumer implementation. That plan is the sole owner of
  Arcadia code, prompts, tests, serialization, container pins, and terminal-save
  behavior.
- [ ] 4.2 Confirm the Arcadia plan covers candidate arrays and pages, image
  selection, reconcile and QA disposition, sole-null handling, branch merge,
  compact terminal-save evidence, persistence, and confidence neutrality.
- [ ] 4.3 Do not implement or commit Internal Arcadia files from this SDK plan.
  Use the SDK source candidate and this plan's cross-repository contract as the
  Arcadia plan's inputs.

## 5. Accept the Internal Arcadia consumer implementation

- [ ] 5.1 Install the recorded SDK source candidate in the Arcadia plan's clean
  environment and verify its hash before consumer tests run.
- [ ] 5.2 Require the Arcadia plan's focused tests to prove all candidate values
  and pages survive reconcile, QA, branch merge, compact terminal save, and
  authorized diagnostics without entering customer JSON.
- [ ] 5.3 Require Arcadia end-to-end cases for a sole required null, sole
  nullable null, two competing candidates, novel reconcile and QA values, and
  more than 30 combined candidate pages. Prove it caps fairly without error,
  and separately prove more than 30 candidates needing distinct images fails
  before the model call.
- [ ] 5.4 Accept the consumer handoff only after the Arcadia plan records its
  exact pushed commit and passing focused, full-suite, protected-case, payload,
  type, and line-ending gates.

## 6. Verify the coordinated behavior

- [ ] 6.1 Run focused Internal Arcadia statement, reconcile prompt, image
  selection, serialization, route merge, save, and trace tests against the
  recorded SDK source candidate.
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
  the exact page numbers attached. Prove `provided_pages` matches only attached
  images and every omitted page remains in `source_pages`.
- [ ] 6.6 Strictly validate this producer OpenSpec change and any consumer
  tracking plan created during implementation. Confirm no customer documents,
  X-Rays, prompts, responses, credentials, or local run artifacts are
  committed.

## 7. Release, pin, and deploy reversibly

- [ ] 7.1 Merge the SDK PR only after the source candidate passes both consumer
  gates. Give the human Fern release owner requested version 3.9.7, the merged
  handwritten source commit, candidate hash, validation evidence, semantic
  compatibility note, and consumer pin requirements. Do not publish from this
  repo.
- [ ] 7.2 After 3.9.7 is published, verify it contains the tested handwritten
  source change. Clean-install it in both consumers and rerun their gates. Do
  not require byte identity with the differently versioned source candidate.
- [ ] 7.3 Require the Internal Arcadia plan to update both dependency writers,
  `requirements.txt` and `Dockerfile.extract`, to the released SDK version.
  Accept the release gate only after that plan builds `Dockerfile.extract`,
  inspects the installed GroundX version, and records the image identity.
- [ ] 7.4 Merge Internal Arcadia, then complete its Task 7 operator handoff
  against `groundx-on-prem` `origin/0.2.7`. Require one immutable image identity
  across all four extract workloads, the prior Helm revision and image digest,
  readiness and installed-SDK proof, and the exact rollback receipt.
- [ ] 7.5 Rerun the ADP side-by-side extraction and capture exact reconcile and
  QA requests, responses, candidate mappings, total document pages, candidate
  source pages, attached pages, and final field values.
- [ ] 7.6 Roll Internal Arcadia back to the prior image and both SDK pins if the
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
