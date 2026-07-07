# Tasks

## 1. Contract Review

- [ ] Read `AGENTS.md`, `.fernignore`, `src/groundx/extract/classes/document.py`,
      `src/groundx/extract/prompt/utility.py`, and existing custom-output tests.
- [ ] Confirm `cashbot-go` producer behavior for JSON array custom-step
      responses remains `_records[]`.
- [ ] Confirm `kind: summary` is a repeated-record step kind in current
      `cashbot-go` behavior, even though the name is easy to misread.
- [ ] Confirm the difference between `keys` and `summary` is backend step
      family selection, not final JSON object-vs-list shape.
- [ ] Confirm docs and tests describe `summary` as a repeated-record output,
      not a singular summary object.
- [ ] Confirm the fix does not introduce a new `shape` field or rename existing
      `kind` values.
- [ ] Confirm direct repeatedness is derived from step kind plus route metadata,
      not solely from `leaf_fields.is_repeated`.
- [ ] Confirm the existing explicit wildcard repeated-path behavior remains
      supported.
- [ ] Confirm the prepared workflow metadata can carry generic
      `workflow.output_relationships` entries with `parent_group`,
      `child_group`, `parent_output_field`, `match_attrs`, and
      `unmatched_child_group`.
- [ ] Confirm `workflow.output_relationships` is included in the custom
      workflow authoring keys and persisted keys in
      `src/groundx/extract/prompt/utility.py`.
- [ ] Confirm normalized relationship metadata is persisted under
      `_groundx_persisted_extract`, reloads without the source YAML, and is
      included in the workflow schema hash.
- [ ] Confirm relationship metadata is generic and does not name Arcadia roles
      or require final groups named `meters` or `charges`.
- [ ] Confirm `workflow.output_relationships` makes SDK `final_output`
      relationship-applied, while `workflow_output` remains available as the
      pre-relationship debug view.
- [ ] Confirm the SDK relationship matcher uses Arcadia-compatible match
      semantics: unwrap extracted-field objects, ignore blank/missing values,
      compare strings case-insensitively, compare numeric ints/floats by value,
      require the same non-empty present match-key set on parent and child, and
      do not date-normalize strings.
- [ ] Confirm existing final-group relationship metadata can be converted to
      `workflow.output_relationships` only when parent information is
      unambiguous, such as harness `passthrough.from`.
- [ ] Audit existing SDK tests and fixtures for direct `kind: keys` or
      `kind: summary` groups that currently expect a singular object, and
      decide whether each should be corrected to an array or changed to
      `kind: instruct`.
- [ ] Confirm release notes call this legacy-compatible with an intentional v1
      shape correction, not blanket backward compatibility.
- [ ] Confirm `openspec/` and touched `src/groundx/extract/` paths survive Fern
      regeneration.

## 2. Failing SDK Tests First

- [ ] Add a failing test for `customChunkOutputs.<step>._records[]` routed to a
      generic repeated final group.
- [ ] Add a failing test for `_records[]` plus a sibling scalar output from the
      same custom step.
- [ ] Add a failing test for a top-level repeated final group assigned to a
      `kind: keys` workflow step.
- [ ] Add a failing test for a top-level repeated final group assigned to a
      `kind: summary` workflow step.
- [ ] Add a failing test proving repeatedness comes from the assigned step kind,
      not from a final group named `meters`, `charges`, or any plural word.
- [ ] Add a failing test proving a plural-looking direct group assigned to
      `kind: instruct` stays singular.
- [ ] Add a failing test for `kind: instruct` object-producing behavior.
- [ ] Add a failing test proving section-level custom outputs copied across
      chunks do not duplicate repeated rows.
- [ ] Add a failing test proving document-level custom outputs copied across
      chunks do not duplicate repeated rows.
- [ ] Add a failing test proving repeated routes prefer `_records[]` over
      direct sibling values for the same output keys.
- [ ] Add a failing test proving singular `instruct` routes ignore `_records[]`
      and read direct scalar/object values.
- [ ] Add a failing test for generic relationship metadata that attaches child
      records under matching parent records using `match_attrs`.
- [ ] Add a failing test proving relationship metadata can create an array
      inside an array by chaining two parent/child relationships.
- [ ] Add a failing test proving unmatched child records remain in
      `unmatched_child_group`.
- [ ] Add a failing test proving a child record that matches multiple parents
      returns a diagnostic instead of silently attaching to one parent.
- [ ] Add failing relationship tests for case-insensitive string matches,
      int/float numeric equality, extracted-field `{"value": ...}` wrappers,
      blank and missing values, missing-on-both fields, missing-on-one-side
      fields, and duplicate parent keys.
- [ ] Add a failing test proving a child and parent only match when they share
      the same non-empty present `match_attrs` key set.
- [ ] Add a failing test proving relationship application returns a
      relationship-applied `final_output` and matching `relationship_output`.
- [ ] Add a failing test proving converted final-group relationship metadata
      produces the same SDK final shape as authored `workflow.output_relationships`.
- [ ] Add a failing test proving final-group metadata with `match_attrs` and
      `passthrough.from` converts into canonical `workflow.output_relationships`.
- [ ] Add a failing test proving final-group metadata with `match_attrs` but no
      parent group is not guessed into a relationship.
- [ ] Add failing prompt-preparation tests proving authored
      `workflow.output_relationships` metadata is validated, persisted,
      reloaded, and included in schema hashing.
- [ ] Add a failing test proving invalid relationship metadata fails clearly
      during preparation.
- [ ] Add a failing test for the public helper import surface and result shape.
- [ ] Update or replace the existing SDK fixture that expects a direct
      `kind: keys` group to load as a singular object.
- [ ] Add a failing test proving pure legacy YAML still loads unchanged.
- [ ] Add a failing test for invalid custom step kind values.

## 3. Implement Generic V1 Reassembly

- [ ] Add or extract a reusable custom-output reassembly helper in the
      hand-written `groundx.extract` layer.
- [ ] Expose `reassemble_custom_outputs` and `CustomOutputReassemblyResult`
      from `groundx.extract.custom_outputs`.
- [ ] Define an import surface usable by SDK `Document.load_xray()`,
      `groundx-studio-harness` diagnostic reconstruction, and
      `internal-arcadia-agents` v1 runtime without depending on private
      `Document` subclass internals.
- [ ] Keep one SDK implementation for custom-output reassembly. SDK, harness,
      and internal Arcadia service call sites may normalize local inputs, but
      must not own separate `_records[]`, `keys`/`summary`, route-correlation, or
      section/document dedupe, or relationship-matching logic.
- [ ] Return SDK `final_output`, optional `relationship_output`,
      `workflow_output`, diagnostics, and route/source metadata from the helper;
      do not mutate `Document` inside the helper.
- [ ] Teach the helper to read direct values, list-valued values, list-of-record
      step outputs, and `_records[]`.
- [ ] For repeated routes, prefer `_records[]` or direct list outputs before
      direct scalar/object fallback.
- [ ] For singular routes, read direct scalar/object values and do not consume
      `_records[]`.
- [ ] Correlate repeated fields by source container, step name, and record index.
- [ ] Preserve scalar outputs beside `_records[]`.
- [ ] Route repeated rows through explicit wildcard paths and top-level
      `kind: keys` / `kind: summary` direct-group paths.
- [ ] Build an effective step-kind lookup from `workflow.custom_steps` so route
      readback can decide output shape without group-name checks or a new
      authored or persisted `shape` field.
- [ ] Define source identity by output level so section-level and document-level
      outputs copied onto chunks are processed once rather than duplicated per
      chunk.
- [ ] Use explicit source identity components: output level, chunk or section
      or document identity, output map, step name, route id or final path, and
      record index.
- [ ] Add a generic relationship metadata parser for
      `workflow.output_relationships`.
- [ ] Add a generic conversion helper that can build normalized
      `workflow.output_relationships` from final-group metadata when parent
      information is unambiguous.
- [ ] Convert harness-style final-group metadata with `match_attrs` and
      `passthrough.from` into canonical relationship metadata, defaulting
      `parent_output_field` and `unmatched_child_group` to the child group name.
- [ ] Do not infer a parent group from `match_attrs` alone.
- [ ] Add `output_relationships` to `_CUSTOM_WORKFLOW_AUTHORING_KEYS` and
      `_CUSTOM_WORKFLOW_PERSISTED_KEYS`.
- [ ] Normalize and validate authored `workflow.output_relationships` during
      prompt preparation.
- [ ] Persist normalized `workflow.output_relationships` under
      `_groundx_persisted_extract`.
- [ ] Include normalized `workflow.output_relationships` in schema hashing.
- [ ] Reload persisted `workflow.output_relationships` without requiring source
      YAML.
- [ ] Apply relationship metadata after route reassembly into SDK
      `final_output` and `relationship_output`, while keeping `workflow_output`
      as the pre-relationship debug view.
- [ ] Match children to parents only when the parent and child share the same
      non-empty present `match_attrs` key set and all present values match.
- [ ] Implement Arcadia-compatible match comparison: unwrap extracted-field
      wrappers, ignore blank/missing values, compare strings case-insensitively,
      compare numeric ints/floats by value, require the same non-empty present
      match-key set on parent and child, and do not date-normalize strings.
- [ ] Preserve unmatched children in `unmatched_child_group` when configured.
- [ ] Return clear diagnostics for invalid relationship metadata, missing parent
      or child groups, and child records that match multiple parents.
- [ ] Support chained relationships so one nested child list can itself be the
      parent of another nested list.
- [ ] Keep `Document.load_custom_outputs()` on the helper instead of maintaining
      a second parser.
- [ ] Do not move prompt authoring, compile/deploy/run ergonomics, scoring,
      Arcadia-specific dedupe, Arcadia requiredness, passthrough, reconcile, QA,
      or final rendering policy into the SDK as part of this change.

## 4. Step Kind Support

- [ ] Keep SDK-supported custom step kinds as `instruct`, `keys`, and
      `summary`.
- [ ] Treat `instruct` as singular-object output.
- [ ] Treat `keys` and `summary` as repeated-record output.
- [ ] Keep `keys` and `summary` distinct backend step-family names while giving
      both repeated-record readback semantics.
- [ ] Ensure prepared workflow metadata exposes each route's effective output
      kind as a derived lookup so readback can detect repeated direct groups
      without final group name checks.
- [ ] Ensure `leaf_fields.is_repeated` does not cause direct `keys` or
      `summary` routes to be treated as singular during readback.
- [ ] Validate unsupported kind values with a clear error.
- [ ] Do not infer repeated groups from names such as `meters`, `charges`,
      `doctors`, or `line_items`.

## 5. Verification

- [ ] `poetry run pytest -rP tests/extract/classes/test_document.py tests/extract/prompt`
- [ ] `poetry run pytest -rP tests/custom tests/extract`
- [ ] `poetry run mypy .`
- [ ] `OPENSPEC_TELEMETRY=0 npx -y @fission-ai/openspec@1.3.1 validate generalize-v1-custom-output-reassembly --strict`
- [ ] `git diff --check`

## 6. Consumer Handoff

- [ ] Document the SDK release version required by `internal-arcadia-agents`.
- [ ] Provide a migration note for Arcadia: v1 custom-output parsing moves to
      SDK helper; legacy YAML parsing remains local; v1 Arcadia and v1 generic
      service paths share the same SDK-backed reassembly path.
- [ ] Update `groundx-studio-harness` local X-Ray reconstruction tests or
      implementation so backend `_records[]` output for `keys` and `summary`
      matches the SDK helper; prefer importing the helper over keeping a local
      copy.
- [ ] Create or update the required harness follow-up change so
      `xray_to_extract.py` delegates to the SDK helper after the fixed SDK is
      available, with parity tests for section/document copied outputs.
- [ ] Confirm harness keeps only file/artifact/scoring/business-logic behavior
      around the helper and removes local custom-output parser ownership after
      the SDK dependency is available.
- [ ] Confirm harness remains responsible for YAML authoring guidance,
      compile/deploy/run scripts, scoring/comparison, and local pilot
      ergonomics rather than becoming the owner of generic v1 readback logic.
- [ ] Confirm no custom step kind rename is required.
- [ ] Publish or hand off a migration note: existing v1 direct `keys` or
      `summary` groups are arrays; use `instruct` for singular direct groups.
