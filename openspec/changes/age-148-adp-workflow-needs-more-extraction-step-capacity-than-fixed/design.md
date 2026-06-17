See proposal.md for motivation and background. This document records the technical decisions for implementing AGE-148 in the groundx-python hand-written layer.

## Goals / Non-Goals

**Goals:**
- Extend `PreparedExtractionYaml` to carry the four new custom-step fields (`custom_template`, `custom_steps`, `output_routes`, `leaf_fields`) through the prepare → persist → submit → readback cycle (FR3).
- Add fail-fast field-level validation for `_custom_steps` entries (name pattern, level enum, kind enum) at parse time in `prepare_extraction_yaml`.
- Extend `Chunk` and `XRayDocument` in `groundx.py` to expose per-step custom X-Ray outputs as optional tolerant-reader fields (FR4).
- Confirm all changed paths are under `.fernignore`-listed directories; confirm `openspec/` survives regeneration.

**Non-Goals:**
- Authoring `outputRoutes[]` or `leafFields[]` routing logic end-to-end (the shapes are carried through as raw list-of-dict pass-throughs; the groundx-api runtime owns their interpretation).
- Any change to the nine fixed `WorkflowSteps` slots or to any generated Fern client file.
- Runtime validation of `CustomWorkflowOutputRoute` / `CustomWorkflowLeafField` entries beyond what the Pydantic models on the generated side enforce (out of scope — groundx-api owns execution validation).

## Decisions

### Decision 1: Reserved-key extension for `_template`, `_custom_steps`, `_output_routes`, `_leaf_fields`

The existing `prepare_extraction_yaml` loop in `utility.py` skips keys listed in `_RESERVED_TOP_LEVEL_KEYS` when building the `raw_groups` dict. The four new custom-step keys follow the same pattern and must be added to this constant (or to a new derived constant that `_RESERVED_TOP_LEVEL_KEYS` is unioned with at parse time). This keeps the group-loading loop clean — the new keys are extracted before the group loop runs, validated, then stored in `PreparedExtractionYaml`.

Alternative considered: treat the keys as top-level metadata (the existing `top_level_metadata_keys` pass-through mechanism). Rejected because that mechanism requires callers to declare the keys at `PromptManager` construction time, making them effectively mandatory to opt into. The custom-step keys have a fixed contract and should be handled unconditionally by the parser.

### Decision 2: Validation in `prepare_extraction_yaml`, not in `PromptManager`

Fail-fast validation (name regex `^[a-z][a-z0-9_]{0,63}$`, level enum `{chunk, section, document}`, kind enum `{instruct, keys, summary}`) runs inside `prepare_extraction_yaml` at the point the `_custom_steps` list is parsed, not deferred to `PromptManager.persisted_workflow_extract_dict` or to the workflow submit call. This means validation is re-run on every `prepare_extraction_yaml` call including the round-trip recovery path (mapping input containing a `_groundx_persisted_extract` blob). The `_custom_steps` list is stored in `PreparedExtractionYaml` as a plain `List[Dict[str, Any]]` — the raw dicts from the authored YAML — after validation passes.

Alternative considered: validate at `PromptManager` submit time only. Rejected because the spec requires rejection "at submit, not execution" but the intent is to catch errors as early as possible, and `prepare_extraction_yaml` is always called before any submission path.

### Decision 3: `PreparedExtractionYaml` gains four new optional dataclass fields

`PreparedExtractionYaml` in `utility.py` gains:

```python
custom_template: Optional[Dict[str, str]] = None
custom_steps: List[Dict[str, Any]] = field(default_factory=list)
output_routes: List[Dict[str, Any]] = field(default_factory=list)
leaf_fields: List[Dict[str, Any]] = field(default_factory=list)
```

`custom_template` is `Optional[Dict[str, str]]` to reflect `WorkflowTemplate` (string→string map). The remaining three fields are lists of raw dicts because the contract shapes are defined in the regenerated Fern client types and we do not hand-write parallel dataclasses for them — the caller passes them directly to the `WorkflowRequest` constructor which owns the final type check.

Alternative considered: use the Fern-generated types (`CustomWorkflowStep`, `CustomWorkflowOutputRoute`, `CustomWorkflowLeafField`) directly in `PreparedExtractionYaml`. Rejected because those types live in the generated `src/groundx/types/` tree which is overwritten on regen; `PreparedExtractionYaml` is hand-written and must not import generated types directly (the `PromptManager` performs the conversion at submit time).

### Decision 4: `PromptManager` reads the four new fields and sets them on `WorkflowRequest` at submit

`PromptManager.persisted_workflow_extract_dict` already surfaces the persisted mapping. The submit side (wherever callers pass this mapping to `workflows.create` / `workflows.update`) needs to also carry `template`, `customSteps`, `outputRoutes`, `leafFields` from `PreparedExtractionYaml`. The `PromptManager` caches the full prepared object; a new accessor (or extension to the cache-update path) exposes the four fields so callers can construct the full `WorkflowRequest`.

Implementation approach: `PromptManager` gains a `custom_workflow_config` method (parallel to `workflow_extract_dict`) that returns a dict with the four new keys populated from the cached `PreparedExtractionYaml` — callers unpack it into the `WorkflowRequest` kwargs. Keys with falsy/empty values are omitted (consistent with existing payload-building convention).

### Decision 5: `Chunk` and `XRayDocument` adopt `extra="allow"` and three new optional fields

`Chunk.model_config` gains `extra="allow"` (it currently has no `model_config` at all — the Pydantic v2 default is `extra="ignore"`). `XRayDocument.model_config` gains `extra="allow"` for the same reason. Both models also get the explicit optional fields so callers can access them by name rather than via the extra-fields mechanism:

- `Chunk.customChunkOutputs: Optional[Dict[str, Any]] = None`
- `Chunk.customSectionOutputs: Optional[Dict[str, Any]] = None`
- `XRayDocument.customDocumentOutputs: Optional[Dict[str, Any]] = None`

`GroundXDocument` is unchanged — it is the thin envelope referencing an `XRayDocument`, not a Pydantic model with field-level parsing.

The upstream X-Ray schemas declare `additionalProperties:true` (confirmed in contract.md). Adding `extra="allow"` is the correct tolerant-reader posture for a consumer of those schemas.

Alternative considered: rely solely on `extra="allow"` without adding named fields. Rejected because named fields make the surface type-safe and visible to mypy; otherwise callers must use `chunk.model_extra["customChunkOutputs"]` which is untyped and fragile.

### Decision 6: `.fernignore` paths — no new entries required

All changed files are inside or at the same level as already-listed `.fernignore` entries:
- `src/groundx/extract/` — covers `utility.py`, `manager.py`, and all subdirs including `classes/groundx.py`.
- `openspec/` — survives regeneration (listed in `.fernignore`).

No new `.fernignore` entries are needed for this change.

### Decision 7: No ADR warranted

This change applies two well-established patterns already present in the codebase (the reserved-keys mechanism + dataclass extension; Pydantic `extra="allow"` for tolerant reading). There is no architectural decision with competing alternatives at a scope that warrants a durable record. A future change that introduced a new submodule or changed the Fern regen pipeline would warrant an ADR; this one does not.

## Risks / Trade-offs

- **`extra="allow"` on `Chunk`:** Previously unknown X-Ray fields were silently dropped; now they are retained in `model_extra`. This is strictly less lossy, but callers iterating `model_dump()` output will see new keys on X-Ray responses that include custom outputs. Existing callers that enumerate chunk fields (e.g. `get_extract()`) use `model_dump(exclude_none=True)` and will therefore start including `customChunkOutputs` / `customSectionOutputs` in their output dicts when present. → Mitigation: the proposal specifies strictly additive behavior; callers must be tolerant-reader-compatible. The `get_extract()` method in `Chunk` uses `model_dump(exclude_none=True)` — custom outputs that are `None` are already excluded, so the behavior for documents without custom steps is unchanged.
- **Round-trip re-validation:** When a workflow's persisted extract blob is recovered via `_fetch_workflow_extract`, `prepare_extraction_yaml` re-validates the `_custom_steps` list in the blob. If a step was authored with a name that was valid at authoring time but the pattern later tightens, re-validation would fail. → Not a real risk for this change (the pattern is fixed in the upstream contract); noted for completeness.
- **`output_routes` / `leaf_fields` as untyped pass-throughs:** These are passed as raw dicts from YAML into the `WorkflowRequest`. Validation of these shapes is groundx-api's responsibility; the extract layer does not validate them beyond confirming they are lists. → Acceptable: the contract confirms these fields are OPTIONAL and their runtime semantics belong to the API.

## Migration Plan

Strictly additive. No migration steps required:
- Existing workflow YAMLs without `_template`, `_custom_steps`, `_output_routes`, `_leaf_fields` are unaffected — the new reserved-key extraction produces empty/None values for all four fields, and the existing group-loading + workflow-groups path is unchanged.
- Existing X-Ray consumers that don't access custom output fields see no behavioral change — `customChunkOutputs`, `customSectionOutputs`, `customDocumentOutputs` default to `None` and `get_extract()` excludes them via `exclude_none=True`.
- Deploy order is unconstrained (additive at all layers).
- Minor version bump to `3.7.0` after merge and SDK regen.

## Open Questions

none
