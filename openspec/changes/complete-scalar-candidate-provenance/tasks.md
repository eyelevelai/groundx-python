# Complete scalar candidate provenance implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` or `superpowers:executing-plans` to
> implement this plan task by task. Use test-first development.

**Goal:** Preserve all scalar values and source pages from section and document
observations without changing repeated-record behavior.

**Architecture:** Change only the route-container boundary and share one
repeated-route predicate with route-value loading. Singular section and document
routes emit every observation. Existing candidate collection deduplicates
values and merges pages. Repeated routes retain producer-copy deduplication.

**Tech stack:** Python 3.11, pytest, Ruff, Mypy, Poetry, OpenSpec 1.3.1.

## Global constraints

- Base work on the implementation branch for
  `delegate-scalar-candidate-resolution-to-agents`, not an unrelated checkout.
- Do not edit or archive any existing OpenSpec change.
- Do not modify generated Fern files or public dataclass shapes.
- Do not change repeated-record, relationship, route-placement, or type-coercion
  behavior.
- Requested release is GroundX Python 3.9.7. Publication remains owned by the
  human release owner.

## Task 1: Lock the lost-provenance behavior

**Files:**

- Modify: `tests/extract/test_custom_output_reassembly.py`
- Exercise: `src/groundx/extract/custom_outputs.py::_route_containers`

**Produces:** Four regressions that distinguish singular observations from
repeated-record copies across section and document routes.

- [ ] Add
  `test_singular_section_route_preserves_candidates_and_pages_across_shared_section_id`.
  Use three chunks with `sectionId: section-1`, pages 12, 14, and 16, and values
  `A`, `A`, and `B`. Assert selected value `A`, selected pages `(12, 14)`, one
  alternative `B` with pages `(16,)`, and provisional final output `A`.
- [ ] Add
  `test_repeated_section_route_still_deduplicates_shared_section_id` using two
  chunks with the same section ID, a `keys` step, a direct top-level final path
  without `*`, and identical `_records`. Assert one final repeated record.
- [ ] Add
  `test_singular_document_route_preserves_candidates_and_chunk_pages`. Include
  the same value at the document root and on pages 12 and 14, plus a competing
  value on page 16. Assert the two candidate values, complete page lists, and no
  invented page for a root-only value.
- [ ] Add
  `test_repeated_document_route_still_deduplicates_copied_payloads` for both a
  wildcard path and a direct top-level `keys` route without `*`. Assert one
  repeated record in each case.
- [ ] Run:
  `poetry run pytest -q tests/extract/test_custom_output_reassembly.py -k 'shared_section_id or document_route'`.
  The singular tests must fail against the current route-container behavior.
  The repeated tests may already pass and record protected behavior.
- [ ] Commit only the tests with message
  `test(extract): expose shared-section scalar provenance loss`.

## Task 2: Preserve singular observations at the section boundary

**Files:**

- Modify: `src/groundx/extract/custom_outputs.py`
- Test: `tests/extract/test_custom_output_reassembly.py`

**Interface:** Private route helpers may accept the existing `step_kinds`
metadata or one precomputed repeated flag. No public interface changes.

- [ ] Add one private repeated-route predicate. It returns true when the step
  kind is `keys` or `summary`, or when parsed `final_path` contains `*`.
- [ ] Use that same predicate in `_route_containers()` and
  `_custom_route_values()` so route shape cannot disagree between the two
  stages.
- [ ] For repeated section routes, retain current
  `custom_output_section_identity()` and `section_seen` behavior.
- [ ] For singular paths, append one `_RouteContainer` for every X-Ray chunk,
  using `_chunk_identity(chunk)` in its internal identity and `_page_numbers(chunk)`
  for provenance. Do not compare values in `_route_containers()`.
- [ ] For singular document routes, append the root observation when present
  and each chunk observation with `_page_numbers(chunk)`. Do not invent root
  page numbers or deduplicate by payload identity before candidate collection.
- [ ] For repeated document routes, retain current payload-identity
  deduplication.
- [ ] Run:
  `poetry run pytest -q tests/extract/test_custom_output_reassembly.py -k 'shared_section_id or document_route or scalar_candidate'`.
  All selected values, alternatives, and page assertions must pass.
- [ ] Run:
  `poetry run pytest -q tests/extract/test_custom_output_reassembly.py`.
  The complete custom-output suite must pass without fixture changes.
- [ ] Commit implementation and focused tests with message
  `fix(extract): preserve scalar pages across section chunks`.

## Task 3: Verify the combined SDK contract

**Files:**

- Verify only. Do not change governed fixtures without explicit human approval.

- [ ] Run changed-file formatting and lint checks:
  `poetry run ruff format --check src/groundx/extract/custom_outputs.py tests/extract/test_custom_output_reassembly.py`
  and
  `poetry run ruff check src/groundx/extract/custom_outputs.py tests/extract/test_custom_output_reassembly.py`.
- [ ] Run `poetry run pytest -q tests/extract`.
- [ ] Run `poetry run mypy .`.
- [ ] Run `bash scripts/check-line-endings.sh` and `git diff --check`.
- [ ] Run
  `OPENSPEC_TELEMETRY=0 npx -y @fission-ai/openspec@1.3.1 validate complete-scalar-candidate-provenance --strict`.
- [ ] Build the same unpublished source candidate used by
  `delegate-scalar-candidate-resolution-to-agents` on Python 3.11. Keep the
  generated package version unchanged. Record its source commit, filename, and
  SHA-256 in the consumer test handoff. Do not publish it.
- [ ] Hand the source candidate to the Internal Arcadia and Studio Harness
  companion changes. Do not request release 3.9.7 until both consumer gates
  pass.
- [ ] After 3.9.7 is published, verify it contains the tested handwritten source
  change and rerun the clean-install consumer gates. Do not require byte
  identity with the differently versioned source candidate.
