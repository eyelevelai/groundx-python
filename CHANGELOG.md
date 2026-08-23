# Changelog

Hand-written SDK surface changes. Generated releases are produced from
[`eyelevel-fern-config`](https://github.com/eyelevelai/eyelevel-fern-config).

## Unreleased

### Deprecated

- `groundx.extract.prepare_extraction_yaml` (and its re-export from
  `groundx.extract.prompt`). Calling it emits a `DeprecationWarning`. Cashbot
  owns workflow validation and compilation: submit authored YAML unchanged
  with `create_extraction_workflow`/`update_extraction_workflow` and read
  workflows back with `load_extraction_definition_from_workflow`.
- Loading authored YAML sources (`path`, `yaml_text`, or an authored mapping)
  through `load_extraction_definition` / `load_extraction_definition_from_yaml`
  runs the deprecated local compiler and emits the same `DeprecationWarning`.
  Workflow readback and `mapping_kind="workflow_extract"` loading do not warn
  and remain supported.
- The relationship-packet spellings `parent_passthrough_attrs` /
  `parentPassthroughAttrs` and `multiple_match_strategy` /
  `multipleMatchStrategy` are compatibility-only transport aliases on
  historical packets. `select_relationship_parent` and custom-output
  reassembly accept and ignore them; they never change parent selection
  (see `openspec/specs/custom-output-readback/spec.md`). Canonical packets
  omit both fields.

## Planned breaking release (not shipped)

The next breaking GroundX Python release removes the deprecated local
authoring surface. Nothing below is removed yet; this section is the removal
plan for `openspec/changes/retire-local-workflow-compiler` (Cashbot
`complete-canonical-workflow-compiler-migration` tasks 11.3/11.6), gated on
supported consumers migrating to raw-YAML authoring or server metadata.

### To be removed

- `prepare_extraction_yaml` and the compiler-only `PreparedExtractionYaml`
  type.
- Authored-YAML extraction definition loading: the `path`, `yaml_text`,
  `mapping` (authored), and `prepared` sources of `load_extraction_definition`
  and `load_extraction_definition_from_yaml`, plus the unused compiled
  authoring helpers in `groundx.extract.workflows`
  (`workflow_kwargs_from_extraction_definition`,
  `ensure_workflow_method_supports_kwargs`, `disabled_fixed_default_steps`).

### To be preserved

- Raw-YAML `create_extraction_workflow` / `update_extraction_workflow`.
- Server workflow readback (`load_extraction_definition_from_workflow`) and
  `mapping_kind="workflow_extract"` loading without recompilation.
- Custom-output reassembly and `select_relationship_parent` consuming
  server-supplied canonical metadata, including the accepted-and-ignored
  handling of the historical relationship-packet spellings above.
