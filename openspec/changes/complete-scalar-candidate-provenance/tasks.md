# Complete scalar candidate provenance implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` or `superpowers:executing-plans` to
> implement this plan task by task. Use test-first development.

**Goal:** Preserve all scalar values and source pages across chunks that share a
section ID without changing repeated-record behavior.

**Architecture:** Change only the section-route container boundary. Singular
routes emit every chunk observation. Existing candidate collection deduplicates
values and merges pages. Repeated routes retain section-ID deduplication.

**Tech stack:** Python 3.9+, pytest, Ruff, Mypy, Poetry, OpenSpec 1.3.1.

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

**Produces:** Two regressions that distinguish singular observations from
repeated-record copies.

- [ ] Add
  `test_singular_section_route_preserves_candidates_and_pages_across_shared_section_id`.
  Use three chunks with `sectionId: section-1`, pages 12, 14, and 16, and values
  `A`, `A`, and `B`. Assert selected value `A`, selected pages `(12, 14)`, one
  alternative `B` with pages `(16,)`, and provisional final output `A`.
- [ ] Add
  `test_repeated_section_route_still_deduplicates_shared_section_id` using two
  chunks with the same section ID and identical `_records`. Assert one final
  repeated record.
- [ ] Run:
  `poetry run pytest -q tests/extract/test_custom_output_reassembly.py -k 'shared_section_id'`.
  Both new tests must fail against the current route-container behavior. The
  singular test must show missing pages or candidates. The repeated test may
  already pass and records the protected behavior.
- [ ] Commit only the tests with message
  `test(extract): expose shared-section scalar provenance loss`.

## Task 2: Preserve singular observations at the section boundary

**Files:**

- Modify: `src/groundx/extract/custom_outputs.py`
- Test: `tests/extract/test_custom_output_reassembly.py`

**Interface:** `_route_containers(xray, route) -> list[_RouteContainer]` keeps
its signature. No public interface changes.

- [ ] In the `level == "section"` branch, determine whether the parsed
  `final_path` contains `*`.
- [ ] For repeated paths, retain the current `custom_output_section_identity()`
  and `section_seen` behavior.
- [ ] For singular paths, append one `_RouteContainer` for every X-Ray chunk,
  using `_chunk_identity(chunk)` in its internal identity and `_page_numbers(chunk)`
  for provenance. Do not compare values in `_route_containers()`.
- [ ] Run:
  `poetry run pytest -q tests/extract/test_custom_output_reassembly.py -k 'shared_section_id or scalar_candidate'`.
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
- [ ] Build the same unpublished candidate wheel used by
  `delegate-scalar-candidate-resolution-to-agents`. Record its source commit,
  filename, and SHA-256 in the consumer test handoff. Do not publish it.
- [ ] Hand the exact wheel to the Internal Arcadia and Studio Harness companion
  changes. Do not request release 3.9.7 until both consumer gates pass.
