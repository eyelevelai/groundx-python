## 1. Extend PreparedExtractionYaml with four new optional fields

- [ ] 1.1 In `src/groundx/extract/prompt/utility.py`, add `_CUSTOM_STEP_KEYS` constant (`{"_template", "_custom_steps", "_output_routes", "_leaf_fields"}`) and union it with `_RESERVED_TOP_LEVEL_KEYS` in the group-loading loop guard inside `prepare_extraction_yaml`
- [ ] 1.2 Add four new dataclass fields to `PreparedExtractionYaml`: `custom_template: Optional[Dict[str, str]] = None`, `custom_steps: List[Dict[str, Any]] = field(default_factory=list)`, `output_routes: List[Dict[str, Any]] = field(default_factory=list)`, `leaf_fields: List[Dict[str, Any]] = field(default_factory=list)`
- [ ] 1.3 Write failing tests in `tests/extract/prompt/test_persisted_workflow_extract.py` covering: (a) YAML with all four custom-step keys → fields populated; (b) YAML without any custom-step keys → fields empty/None; (c) existing group/workflow-group behavior unchanged
- [ ] 1.4 Verify tests fail for the right reason (fields not yet populated)

## 2. Parse and extract custom-step keys in prepare_extraction_yaml

- [ ] 2.1 In `prepare_extraction_yaml`, after extracting `top_level_metadata` and before the group-loading loop, extract `_template`, `_custom_steps`, `_output_routes`, `_leaf_fields` from `data` into local variables
- [ ] 2.2 Return updated `PreparedExtractionYaml` with the four new fields populated from those local variables; ensure the `_groundx_persisted_extract` round-trip path (`data = data[_PERSISTED_WORKFLOW_EXTRACT_KEY]`) also extracts these keys from the recovered blob
- [ ] 2.3 Run tests from task 1.3 — confirm they pass

## 3. Add fail-fast validation for _custom_steps entries

- [ ] 3.1 Write failing tests in `tests/extract/prompt/test_persisted_workflow_extract.py` for: (a) `name` with a space raises `ValueError`; (b) `level: "paragraph"` raises `ValueError`; (c) `kind: "embed"` raises `ValueError`; (d) valid step `{name: "adp_chunk_01", level: "chunk", kind: "instruct"}` passes
- [ ] 3.2 Verify tests fail for the right reason (no validation code yet)
- [ ] 3.3 Implement `_validate_custom_step(step: Dict[str, Any], idx: int) -> None` in `utility.py` that enforces: `name` matches `^[a-z][a-z0-9_]{0,63}$`, `level` in `{"chunk", "section", "document"}`, `kind` in `{"instruct", "keys", "summary"}`; raises `ValueError` naming the step name and invalid field
- [ ] 3.4 Call `_validate_custom_step` for each entry in the extracted `_custom_steps` list inside `prepare_extraction_yaml`, before populating `PreparedExtractionYaml`
- [ ] 3.5 Run tests from task 3.1 — confirm they pass; run the full extract test suite (`poetry run pytest -rP -n auto tests/extract/`) and confirm it stays green

## 4. Add custom_workflow_config accessor to PromptManager

- [ ] 4.1 In `src/groundx/extract/prompt/manager.py`, add a `_prepared_custom_config` cache dict (`Dict[str, Dict[str, Any]]`) alongside the existing per-workflow caches
- [ ] 4.2 In `cache_workflow`, after populating `_persisted_workflow_extract`, also store the four new fields from the `PreparedExtractionYaml` into `_prepared_custom_config[workflow_id]` as a dict: `{"template": ..., "customSteps": ..., "outputRoutes": ..., "leafFields": ...}` — omitting keys with falsy/empty values (consistent with the existing payload-building convention)
- [ ] 4.3 Write failing tests in `tests/extract/prompt/test_manager.py` for: (a) `custom_workflow_config()` returns correct keys when YAML contains `_custom_steps`; (b) `custom_workflow_config()` returns empty dict (or omits keys) when YAML has no custom-step keys; (c) mapping round-trip: a persisted extract blob with `_custom_steps` restores the same `customSteps` in the config
- [ ] 4.4 Verify tests fail for the right reason
- [ ] 4.5 Implement `PromptManager.custom_workflow_config(file_name=None, workflow_id=None) -> Dict[str, Any]` that calls `cache_workflow` and returns a deep copy of the stored config dict for the resolved `workflow_id`
- [ ] 4.6 Run tests from task 4.3 — confirm they pass

## 5. Extend Chunk with custom output fields and extra="allow"

- [ ] 5.1 Write failing tests in `tests/extract/classes/test_groundx.py` for: (a) `Chunk(**{..., "customChunkOutputs": {"adp_chunk_01": {"plan_type": "401k"}}}).customChunkOutputs` equals the input dict; (b) `Chunk(**{..., "customSectionOutputs": {"adp_section_01": {"section_name": "Contributions"}}}).customSectionOutputs` equals the input dict; (c) chunk without either key has both fields as `None`; (d) chunk with an unknown field (e.g. `"futureField": "value"`) does NOT raise `ValidationError`
- [ ] 5.2 Verify tests fail for the right reason (fields absent, extra="ignore" drops unknowns)
- [ ] 5.3 In `src/groundx/extract/classes/groundx.py`, add `model_config = ConfigDict(extra="allow")` to `Chunk` and add `customChunkOutputs: Optional[Dict[str, Any]] = None` and `customSectionOutputs: Optional[Dict[str, Any]] = None` fields
- [ ] 5.4 Run tests from task 5.1 — confirm they pass; run `poetry run mypy src/groundx/extract/classes/groundx.py` and confirm no new errors

## 6. Extend XRayDocument with customDocumentOutputs and extra="allow"

- [ ] 6.1 Write failing tests in `tests/extract/classes/test_groundx.py` for: (a) `XRayDocument(**{..., "customDocumentOutputs": {"adp_doc_01": {"plan_name": "ADP 401k"}}}).customDocumentOutputs` equals the input dict; (b) `XRayDocument` without the key has `customDocumentOutputs` as `None`; (c) unknown document-level field does NOT raise `ValidationError`; (d) `XRayDocument.download` returns a model where `chunks[0].customChunkOutputs` is accessible when the X-Ray JSON contains it
- [ ] 6.2 Verify tests fail for the right reason
- [ ] 6.3 In `src/groundx/extract/classes/groundx.py`, add `model_config = ConfigDict(extra="allow")` to `XRayDocument` and add `customDocumentOutputs: Optional[Dict[str, Any]] = None`
- [ ] 6.4 Run tests from task 6.1 — confirm they pass; run `poetry run mypy src/groundx/extract/classes/groundx.py` and confirm no new errors

## 7. Verify backward-compatibility scenarios pass

- [ ] 7.1 Run existing extract test suite in full (`poetry run pytest -rP -n auto tests/extract/`) — all existing tests must remain green
- [ ] 7.2 Add an explicit backward-compat regression test confirming a legacy YAML (no custom-step keys) produces the same `groups`, `workflow_groups`, and `workflow_field_paths` as before, and that `workflow_extract_dict` output is unchanged

## 8. Type-check and full CI gate

- [ ] 8.1 Run `poetry run mypy .` (without `--extras extract`) — must exit 0 with no new errors
- [ ] 8.2 Run `poetry run pytest -rP -n auto .` — full suite green
- [ ] 8.3 Run `openspec validate --type change "age-148-adp-workflow-needs-more-extraction-step-capacity-than-fixed"` — must pass

---

See workspace `openspec/changes/age-148-adp-workflow-needs-more-extraction-step-capacity-than-fixed/tasks.md` for cross-service coordination and deferred items.
