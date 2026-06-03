# Tasks: Extract YAML Pseudo Groups

## Execution Plan

## Between-Task Adversarial Review

After each checklist item is completed, pause before starting the next item and
review the completed work adversarially:

- Does the change preserve the final data-object contract: top-level real groups
  represent final output, while pseudo groups are workflow-only?
- Does workflow generation use pseudo groups when present and legacy final groups
  when absent?
- Does every workflow field have a deterministic route back to exactly one final
  data path?
- Does every workflow group expose deterministic effective workflow metadata,
  with pseudo-group metadata overriding final-group metadata where appropriate?
- Do ambiguous metadata inheritance cases fail instead of guessing?
- Did the task introduce hidden runtime behavior, cross-file includes, silent
  overwrite semantics, or dependency creep?
- Does YAML parsing fail on duplicate keys before composition can hide them?
- Does legacy YAML without `_pseudo_groups`, `_defs`, or `include` still produce
  the same groups, fields, prompts, and workflow extract shape?
- Do tests prove both the happy path and the likely failure mode for this task?
- Does the current plan still point to the right docs, harness, and Arcadia
  follow-up?

If the review finds an issue, fix or record it before executing the next task.

### Phase 1: SDK Contract And Implementation

- [ ] Confirm the exact public syntax in
      `/Users/benjaminfletcher/git/groundx-python/openspec/changes/extract-yaml-group-fragments/design.md`
      before editing code.
- [ ] Adversarially review the confirmed syntax against current
      `groundx.extract` loader and PromptManager behavior before writing tests.
- [ ] Add fixture YAML for `_pseudo_groups` covering both scenarios:
      splitting one large final group into smaller workflow groups and merging
      two small sibling final groups into one workflow group.
- [ ] Identify existing legacy YAML fixtures without `_pseudo_groups`, `_defs`,
      or `include` and add golden assertions for group keys, field keys, prompt
      values, `workflow_extract_dict()` shape, and identity route map.
- [ ] Add failing tests for final-data shape: `load_from_yaml()` returns only
      final groups, never `_pseudo_groups`.
- [ ] Add failing tests for workflow shape: `workflow_extract_dict()` uses pseudo
      workflow groups when `_pseudo_groups` is present.
- [ ] Add failing tests that pseudo workflow groups are addressable by their
      authored names through workflow-facing accessors.
- [ ] Add failing tests for residual workflow groups: routed fields are removed
      from their final workflow group, while unrouted final fields still run
      under residual final workflow groups.
- [ ] Add failing tests for route-map behavior: pseudo-group aliases and
      residual final fields map to the correct final data paths.
- [ ] Add failing tests for pseudo-group prompt behavior: single-parent pseudo
      groups can inherit parent prompt, multi-parent pseudo groups require an
      explicit mapping-shaped prompt.
- [ ] Add failing tests that a split pseudo group inherits shared parent prompt
      context when it references one final parent and omits its own prompt.
- [ ] Add failing tests for validation errors: unknown path, duplicate route,
      malformed `_pseudo_groups`, malformed pseudo field, pseudo field prompt
      override, pseudo group/final group name collision, scalar `prompt:`
      shorthand, malformed `_defs`, malformed `include`, unsupported `_defs`
      keys, pseudo-group `include`, and duplicate final field names.
- [ ] Add failing tests for duplicate YAML keys before composition: duplicate
      top-level group keys, duplicate `_pseudo_groups` names, duplicate pseudo
      field keys, duplicate `_defs` fragment names, duplicate final field names,
      and duplicate keys inside a field prompt mapping.
- [ ] Add failing tests for `prepare_extraction_yaml()` metadata separation:
      harness-style `domain`, final-group metadata, and pseudo-group metadata are
      separated from final/workflow groups while legacy YAML with no metadata
      remains unchanged.
- [ ] Add failing tests for effective `slot` metadata positive cases:
      no-pseudo final group keeps its slot, pseudo explicit slot overrides final
      group slot, single-parent pseudo group inherits final group slot,
      multi-parent pseudo group inherits when all parents share the same slot,
      pseudo group remains unset when no referenced parent has a slot, multiple
      pseudo groups can share the same slot, and sibling pseudo groups can mix
      inherited and explicit overridden slots from the same parent.
- [ ] Add failing tests for effective `slot` metadata conflict cases:
      multi-parent pseudo group without explicit slot where parent slots differ,
      and multi-parent pseudo group without explicit slot where only some
      parents have slots.
- [ ] Add failing tests that `slot: null` is treated as unset for inheritance,
      while empty-string slot values are preserved for harness validation rather
      than interpreted by the SDK.
- [ ] Adversarially review the failing tests for gaps before implementing the
      loader change.
- [ ] Implement duplicate-key-aware YAML parsing in
      `src/groundx/extract/prompt/utility.py`.
- [ ] Implement final group preparation, `_defs` field composition, and
      `_pseudo_groups` workflow routing in `utility.py`.
- [ ] Ensure `_defs` / `include` compose only into final groups before
      pseudo-group routing; pseudo groups route to final fields and cannot
      include `_defs` directly.
- [ ] Materialize pseudo groups as normal group-shaped workflow mappings keyed
      by pseudo-group name, including single-parent inherited prompt context
      when no pseudo prompt is declared.
- [ ] Add the shared SDK helper `prepare_extraction_yaml()` and, if useful,
      `load_from_mapping()` for already-prepared mappings.
- [ ] Add `PreparedExtractionYaml` fields for final groups, workflow groups,
      pseudo groups, workflow field paths, top-level metadata, final-group
      metadata, pseudo-group metadata, and resolved workflow-group metadata.
- [ ] Implement workflow metadata resolution for caller-provided metadata keys,
      including the `slot` precedence/conflict matrix in the design.
- [ ] Export `PreparedExtractionYaml` and `prepare_extraction_yaml` from
      `groundx.extract` via `src/groundx/extract/__init__.py` and add a smoke
      test for that stable public import surface.
- [ ] Keep `load_from_yaml(raw_yaml)` returning final data groups only.
- [ ] Update `PromptManager` so workflow-facing methods use prepared workflow
      groups and new final-data accessors expose final data groups.
- [ ] Add an SDK route-map accessor for Arcadia reassembly.
- [ ] Add an SDK workflow-group metadata accessor for harness workflow
      compilation.
- [ ] Keep `Group`, `ExtractedField`, and workflow serialization behavior
      unchanged unless a test demonstrates a required integration fix.
- [ ] Adversarially review the implementation against duplicate-route,
      residual-group, unknown-path, metadata-placement, and legacy-compatibility
      edge cases before running the full extract test gate.
- [ ] Run the narrow prompt-loader tests.
- [ ] Run `poetry run pytest -rP -n auto tests/extract`.
- [ ] Run `poetry run pytest -rP -n auto .`.
- [ ] Run `poetry run mypy .`.
- [ ] Record final syntax and validation behavior in this change folder if the
      implementation differs from the planned contract.
- [ ] Record the legacy compatibility evidence: which fixtures were checked and
      what output shape remained unchanged.
- [ ] Adversarially review Phase 1 closeout before handing off to docs, harness,
      and Arcadia: verify tests, error semantics, final data structure, workflow
      group structure, and route-map semantics.

### Phase 2: Public Docs Handoff

Start only after Phase 1 is green.

- [ ] Execute the Fern documentation plan in
      `/Users/benjaminfletcher/git/eyelevel-fern-config/openspec/changes/document-extraction-workflow-walkthrough/tasks.md`.
- [ ] Ensure the public guide describes `_pseudo_groups` as available SDK
      behavior using present-tense product language.
- [ ] Ensure public examples keep final groups as the final output object.
- [ ] Ensure public examples show both pseudo-group scenarios: splitting one
      large final group and merging small sibling final groups.
- [ ] Ensure public examples use mapping-shaped `prompt:` objects, not scalar
      prompt shorthand.
- [ ] Ensure docs show the workflow group shape, final data shape, and route-map
      role in reassembly.
- [ ] Adversarially review the completed docs handoff for future-tense wording,
      feature-only framing, and any claim that pseudo groups appear in final
      output.

### Phase 3: Harness Skill And Workflow Guide Handoff

Start only after Phase 1 is green and the public docs contract is drafted or
merged.

- [ ] Execute the harness plan in
      `/Users/benjaminfletcher/git/groundx-studio-harness/openspec/changes/extraction-yaml-fragments-and-howto/tasks.md`.
- [ ] Require the harness adversarial review before changing the extraction
      skill.
- [ ] Update the harness skill to reference the public docs as canonical syntax
      and keep harness examples aligned with the SDK tests.
- [ ] Ensure harness code consumes the shared SDK helper rather than
      reimplementing pseudo-group routing or effective workflow metadata
      precedence, except for harness-owned slot/domain value interpretation.
- [ ] Tell the harness plan the exact SDK release/minimum version that contains
      the shared helper so harness templates do not import it from an older
      allowed `groundx[extract]` version.
- [ ] Ensure harness examples keep `_defs` fields-only, with reusable prompt text
      outside `_defs`, and no scalar prompt shorthand.
- [ ] Ensure harness examples explain that pseudo groups are workflow-only groups
      that must be reassembled into final data groups.
- [ ] Adversarially review the completed harness handoff for business-logic
      boundary drift, generated mirror drift, and any pseudo-group-as-output
      language.

### Phase 4: Arcadia Reassembly Handoff

Start only after Phase 1 is green and harness workflow artifacts expose the SDK
route map.

- [ ] Execute the Arcadia plan in
      `/Users/benjaminfletcher/git/internal-arcadia-agents/openspec/changes/extraction-pseudo-groups-reassembly/tasks.md`.
- [ ] Ensure Arcadia consumes the SDK route map or equivalent compiled metadata
      to reassemble pseudo-group extraction output into the final data object.
- [ ] Ensure Arcadia tests cover both splitting one large final group and merging
      small sibling final groups into one pseudo group.
- [ ] Adversarially review Arcadia closeout for duplicate-route handling,
      missing pseudo-group outputs, conflict semantics, reconcile/QA boundary
      drift, and final object compatibility.

### Phase 5: Closeout

- [ ] Confirm all repo-local plans are either complete or explicitly marked with
      remaining follow-up.
- [ ] Adversarially review the full cross-repo trail before closeout: SDK
      behavior, public docs, harness skill, Arcadia reassembly, generated
      mirrors, validation evidence, and unresolved risks.
- [ ] Summarize implemented SDK behavior, docs updates, harness updates, Arcadia
      updates, and all validation commands in the final handoff.
