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
  with pseudo-group workflow metadata overriding inherited final-group workflow
  metadata where appropriate?
- Are final-group/business metadata and workflow metadata separated so keys like
  `unique_attrs`, `match_attrs`, `conflict_attrs`, `passthrough`, and `pipeline`
  do not leak onto pseudo workflow groups unless explicitly workflow-scoped?
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

- [x] Confirm the exact public syntax in
      `/Users/benjaminfletcher/git/groundx-python/openspec/changes/extract-yaml-group-fragments/design.md`
      before editing code.
- [x] Inspect the current partial `prepare_extraction_yaml()` implementation and
      exports. Record the stale surfaces that must be replaced: dot-separated
      routes, `group_metadata`, `pseudo_group_metadata`,
      `group_metadata_keys`, `pseudo_group_metadata_keys`, and missing
      `FinalFieldPath` public exports.
- [x] Adversarially review the confirmed syntax against current
      `groundx.extract` loader and PromptManager behavior before writing tests.
- [x] Add fixture YAML for `_pseudo_groups` covering both scenarios:
      splitting one large final group into smaller workflow groups and merging
      two small sibling final groups into one workflow group.
- [x] Identify existing legacy YAML fixtures without `_pseudo_groups`, `_defs`,
      or `include` and add golden assertions for group keys, field keys, prompt
      values, `workflow_extract_dict()` shape, and identity route map.
- [x] Add failing tests for final-data shape: `load_from_yaml()` returns only
      final groups, never `_pseudo_groups`.
- [x] Add failing tests for workflow shape: `workflow_extract_dict()` uses pseudo
      workflow groups when `_pseudo_groups` is present.
- [x] Add failing tests that pseudo workflow groups are addressable by their
      authored names through workflow-facing accessors.
- [x] Add failing tests for residual workflow groups: routed fields are removed
      from their final workflow group, while unrouted final fields still run
      under residual final workflow groups.
- [x] Add failing tests for route-map behavior: pseudo-group aliases and
      residual final fields map to the correct final-output JSON Pointer paths.
- [x] Add failing tests for route path parsing: paths use JSON Pointer syntax,
      escaped `~1` and `~0` segments resolve correctly, dots in group or field
      names have no special meaning, malformed escapes fail, and unsupported
      nested/repeating paths fail until the final schema model supports them.
- [x] Add failing tests for pseudo-group prompt behavior: single-parent pseudo
      groups can inherit parent prompt, multi-parent pseudo groups require an
      explicit mapping-shaped prompt.
- [x] Add failing tests that a split pseudo group inherits shared parent prompt
      context when it references one final parent and omits its own prompt.
- [x] Deferred granular validation-error fixture expansion to
      `/Users/benjaminfletcher/git/groundx-python/openspec/changes/extraction-pseudo-group-operational-closeout/tasks.md`:
      unknown path, duplicate route,
      malformed `_pseudo_groups`, missing pseudo-group `fields`, empty
      pseudo-group `fields`, unsupported pseudo-group top-level metadata,
      malformed pseudo field, pseudo field prompt override, pseudo group/final
      group name collision, scalar `prompt:` shorthand, malformed `_defs`,
      malformed `include`, unsupported `_defs` keys, pseudo-group `include`,
      and duplicate final field names.
- [x] Deferred granular duplicate-key fixture expansion to
      `/Users/benjaminfletcher/git/groundx-python/openspec/changes/extraction-pseudo-group-operational-closeout/tasks.md`:
      duplicate
      top-level group keys, duplicate `_pseudo_groups` names, duplicate pseudo
      field keys, duplicate `_defs` fragment names, duplicate final field names,
      and duplicate keys inside a field prompt mapping.
- [x] Add failing tests that YAML merge keys (`<<`) are rejected before
      composition, while ordinary anchors/aliases do not create shared mutable
      prepared mappings.
- [x] Add failing tests that recursive YAML aliases or cyclic YAML
      object graphs raise `ValueError` before composition.
- [x] Add failing tests for `prepare_extraction_yaml()` metadata separation:
      harness-style `domain`, final-group/business metadata, and workflow-group
      metadata are separated from final/workflow groups while legacy YAML with no
      metadata remains unchanged.
- [x] Add failing tests proving v1 rejects arbitrary pseudo-group author
      metadata. Pseudo groups may contain only `prompt`, `fields`, and
      caller-declared workflow metadata keys such as `slot`.
- [x] Add failing tests that final-group/business metadata keys such as
      `unique_attrs`, `match_attrs`, `conflict_attrs`, `passthrough`, and
      `pipeline` remain on the final metadata surface and are not inherited by
      pseudo workflow groups unless the caller explicitly opts into a
      workflow-scoped key.
- [x] Add failing tests for effective `slot` metadata positive cases:
      no-pseudo final group keeps its slot, pseudo explicit slot overrides final
      group slot, single-parent pseudo group inherits final group slot,
      multi-parent pseudo group inherits when all parents share the same slot,
      pseudo group remains unset when no referenced parent has a slot, multiple
      pseudo groups can share the same slot, and sibling pseudo groups can mix
      inherited and explicit overridden slots from the same parent.
- [x] Add failing tests for effective `slot` metadata conflict cases:
      multi-parent pseudo group without explicit slot where parent slots differ,
      and multi-parent pseudo group without explicit slot where only some
      parents have slots.
- [x] Deferred `slot: null` and empty-string slot fixture expansion to
      `/Users/benjaminfletcher/git/groundx-python/openspec/changes/extraction-pseudo-group-operational-closeout/tasks.md`:
      `slot: null` should be treated as unset for inheritance,
      while empty-string slot values are preserved for harness validation rather
      than interpreted by the SDK.
- [x] Adversarially review the failing tests for gaps before implementing the
      loader change.
- [x] Implement duplicate-key-aware YAML parsing in
      `src/groundx/extract/prompt/utility.py`.
- [x] Implement `FinalFieldPath` parsing/serialization for JSON Pointer route
      paths in final-output coordinates, including public `parse()`,
      `to_pointer()`, `__str__()`, equality, and malformed-escape validation.
- [x] Implement final group preparation, `_defs` field composition, and
      `_pseudo_groups` workflow routing in `utility.py`.
- [x] Ensure `_defs` / `include` compose only into final groups before
      pseudo-group routing; pseudo groups route to final fields and cannot
      include `_defs` directly.
- [x] Materialize pseudo groups as normal group-shaped workflow mappings keyed
      by pseudo-group name, including single-parent inherited prompt context
      when no pseudo prompt is declared.
- [x] Add the shared SDK helper `prepare_extraction_yaml()` and, if useful,
      `load_from_mapping()` for already-prepared mappings.
- [x] Add `PreparedExtractionYaml` fields for final groups, workflow groups,
      pseudo groups, workflow field paths, top-level metadata, final-group
      metadata, and resolved workflow-group metadata. Do not expose a public
      `pseudo_group_metadata` field in v1.
- [x] Remove or replace the old partial-helper API surface so callers cannot
      keep using stale `group_metadata`, `pseudo_group_metadata`,
      dot-separated route paths, or old metadata-key argument names by accident.
- [x] Keep `PreparedExtractionYaml` group surfaces as deep-copied raw mappings,
      and keep parsed `Group` model objects behind `load_from_mapping()` and
      `PromptManager` accessors.
- [x] Implement workflow metadata resolution for caller-provided metadata keys,
      including the `slot` precedence/conflict matrix in the design.
- [x] Keep final-group/business metadata resolution separate from workflow
      metadata resolution; do not copy final-only metadata onto pseudo workflow
      groups.
- [x] Export `FinalFieldPath`, `PreparedExtractionYaml`, and
      `prepare_extraction_yaml` from `groundx.extract` via
      `src/groundx/extract/__init__.py` and add a smoke test for that stable
      public import surface.
- [x] Keep `load_from_yaml(raw_yaml)` returning final data groups only.
- [x] Update `PromptManager` so workflow-facing methods use prepared workflow
      groups and new final-data accessors expose final data groups.
- [x] Add an SDK route-map accessor for Arcadia reassembly.
- [x] Document and test that `PreparedExtractionYaml.groups` remains the
      final-field schema surface Arcadia can use for field-level requiredness or
      null-policy signals during reassembly.
- [x] Document the versioned serialized handoff artifact that harness should
      persist for Arcadia, including `workflow_field_paths`, prepared final
      groups or equivalent final field schema, and both metadata surfaces.
- [x] Add an SDK workflow-group metadata accessor for harness workflow
      compilation.
- [x] Keep `Group`, `ExtractedField`, and workflow serialization behavior
      unchanged unless a test demonstrates a required integration fix.
- [x] Adversarially review the implementation against duplicate-route,
      residual-group, unknown-path, metadata-placement, and legacy-compatibility
      edge cases before running the full extract test gate.
- [x] Run the narrow prompt-loader tests.
- [x] Run `poetry run pytest -rP -n auto tests/extract`.
- [x] Run `poetry run pytest -rP -n auto .`.
- [x] Run `poetry run mypy .`.
- [x] Run `poetry run pyright -p pyrightconfig.json`.
- [x] When validating the local `extract-sdk` symlink workspace, run
      `npx -y pyright@latest -p /Users/benjaminfletcher/git/extract-sdk/pyrightconfig.json`
      as an editor/Pylance parity check. Do not treat this absolute-path command
      as a portable repo gate.
- [x] Record final syntax and validation behavior in this change folder if the
      implementation differs from the planned contract.
- [x] Record the legacy compatibility evidence: which fixtures were checked and
      what output shape remained unchanged.
- [x] Adversarially review Phase 1 closeout before handing off to docs, harness,
      and Arcadia: verify tests, error semantics, final data structure, workflow
      group structure, and route-map semantics.

### Phase 2: Public Docs Handoff

Start only after Phase 1 is green. Public docs may be drafted here, but must not
be published or described as complete end-to-end deployed behavior until Arcadia
reassembly is implemented and tested, or the public copy explicitly excludes
unavailable reassembly behavior.

- [x] Execute the Fern documentation plan in
      `/Users/benjaminfletcher/git/eyelevel-fern-config/openspec/changes/document-extraction-workflow-walkthrough/tasks.md`.
- [x] Ensure the public guide describes `_pseudo_groups` as available SDK
      behavior using present-tense product language.
- [x] Ensure public examples keep final groups as the final output object.
- [x] Ensure public examples show both pseudo-group scenarios: splitting one
      large final group and merging small sibling final groups.
- [x] Ensure public examples use mapping-shaped `prompt:` objects, not scalar
      prompt shorthand.
- [x] Ensure docs show the workflow group shape, final data shape, and route-map
      role in reassembly.
- [x] Ensure docs show route-map paths as final-output JSON Pointers, not
      dot-separated strings.
- [x] Adversarially review the completed docs handoff for future-tense wording,
      feature-only framing, and any claim that pseudo groups appear in final
      output.

### Phase 3: Harness Skill And Workflow Guide Handoff

Start only after Phase 1 is green and the public docs contract is drafted or
merged. Harness source changes may be prepared before Arcadia, but public plugin
mirror sync and closeout must wait for Arcadia reassembly tests unless the
shipped skill explicitly excludes unavailable reassembly behavior.

- [x] Execute the harness plan in
      `/Users/benjaminfletcher/git/groundx-studio-harness/openspec/changes/extraction-yaml-fragments-and-howto/tasks.md`.
- [x] Require the harness adversarial review before changing the extraction
      skill.
- [x] Update the harness skill to reference the public docs as canonical syntax
      and keep harness examples aligned with the SDK tests.
- [x] Ensure harness code consumes the shared SDK helper rather than
      reimplementing pseudo-group routing or effective workflow metadata
      precedence, except for harness-owned slot/domain value interpretation.
- [x] Tell the harness plan the exact SDK release/minimum version that contains
      the shared helper so harness templates do not import it from an older
      allowed `groundx[extract]` version.
- [x] Ensure harness examples keep `_defs` fields-only, with reusable prompt text
      outside `_defs`, and no scalar prompt shorthand.
- [x] Ensure harness examples explain that pseudo groups are workflow-only groups
      that must be reassembled into final data groups.
- [x] Ensure harness route-map examples and artifacts use final-output JSON
      Pointer paths, not dot-separated strings.
- [x] Adversarially review the completed harness handoff for business-logic
      boundary drift, generated mirror drift, and any pseudo-group-as-output
      language.

### Phase 4: Arcadia Reassembly Handoff

Start only after Phase 1 is green and harness workflow artifacts expose the SDK
route map.

- [x] Execute the Arcadia plan in
      `/Users/benjaminfletcher/git/internal-arcadia-agents/openspec/changes/extraction-pseudo-groups-reassembly/tasks.md`.
- [x] Ensure Arcadia consumes the SDK route map or equivalent compiled metadata
      to reassemble pseudo-group extraction output into the final data object.
- [x] Ensure Arcadia tests cover both splitting one large final group and merging
      small sibling final groups into one pseudo group.
- [x] Adversarially review Arcadia closeout for duplicate-route handling,
      missing pseudo-group outputs, conflict semantics, reconcile/QA boundary
      drift, and final object compatibility.

### Phase 5: Closeout

- [x] Confirm all repo-local plans are either complete or explicitly marked with
      remaining follow-up.
- [x] Adversarially review the full cross-repo trail before closeout: SDK
      behavior, public docs, harness skill, Arcadia reassembly, generated
      mirrors, validation evidence, and unresolved risks.
- [x] Summarize implemented SDK behavior, docs updates, harness updates, Arcadia
      updates, and all validation commands in the final handoff.

## Closeout Notes

- SDK behavior landed in `src/groundx/extract/prompt/utility.py` and
  `src/groundx/extract/prompt/manager.py`, with public exports from
  `groundx.extract` and `groundx.extract.prompt`.
- Legacy compatibility evidence is covered by `tests/extract/prompt` identity
  route-map tests, legacy `load_from_yaml()` assertions, workflow extract shape
  checks, and the full SDK test gates recorded in this plan.
- The docs handoff is saved in
  `/Users/benjaminfletcher/git/eyelevel-fern-config/openspec/changes/document-extraction-workflow-walkthrough/`.
- The harness handoff is saved in
  `/Users/benjaminfletcher/git/groundx-studio-harness/openspec/changes/extraction-yaml-fragments-and-howto/`.
- The Arcadia handoff is saved in
  `/Users/benjaminfletcher/git/internal-arcadia-agents/openspec/changes/extraction-pseudo-groups-reassembly/`.
- Remaining unchecked SDK checklist items are granular validation surfaces that
  were not all exhaustively enumerated as separate tests in this pass, not known
  regressions. The implemented tests cover the critical shipped contract:
  final/workflow group separation, `_defs`, route maps, duplicate keys,
  duplicate routes, metadata separation, slot conflict behavior, YAML merge-key
  rejection, recursive alias rejection, and legacy no-pseudo behavior.
- Broad `ruff check src/groundx/extract tests/extract` currently fails on
  existing generated-style issues outside this change. Touched-file Ruff passes
  for the SDK files modified in this pass.
