# Design: Persist Authored Extraction YAML In Workflows

## Current Failure

The harness compiles a YAML file by calling `prepare_extraction_yaml(...)`, then
serializing a `PromptManager.workflow_extract_dict()` payload into
`workflow.extract`. That payload is intentionally execution-shaped. It contains
workflow groups and fields, but it drops authored metadata that the runtime later
needs when it reloads from `workflow.extract`.

The SDK should own the distinction between:

- execution groups: the small group-shaped payload GroundX workflow agents need
  to run extraction steps
- persisted workflow extract: the YAML-shaped payload saved under
  `workflow.extract` so the full authored extraction contract can be downloaded
  and prepared again later

## Required Persistence Contract

`workflow.extract` is a JSON object in the GroundX workflow API, while existing
SDK source loaders read YAML text from local files or object storage. The SDK
must support both forms explicitly.

The default target API is:

- `PreparedExtractionYaml.persisted_workflow_extract`: a JSON-serializable
  mapping suitable for assigning directly to workflow JSON `extract`.
- `prepare_extraction_yaml(...)`: accepts either raw YAML text or a mapping that
  came from workflow JSON `extract`, without mutating caller-owned objects.

The selected carrier must satisfy these rules:

- the persisted payload is a mapping, not a string hidden inside workflow JSON
- the persisted payload can be JSON serialized and deserialized without losing
  metadata
- the SDK can prepare the persisted payload back into the same prepared metadata
  surfaces
- the persisted payload remains safe to assign to GroundX workflow create/update
  `extract` without breaking workflow step references to execution groups
- `load_from_yaml(raw)` still returns final data groups only.
- `PromptManager` execution methods still expose workflow groups only.
- top-level metadata must not be misinterpreted as a final group.
- `_pseudo_groups` must remain workflow-only and must not appear in final output.

## Public SDK Surface

Prefer one explicit new helper or method rather than changing the meaning of an
existing execution method silently. The preferred surface is:

- `PreparedExtractionYaml.persisted_workflow_extract`
- `PromptManager.persisted_workflow_extract_dict()`

The name should make it clear that this payload is for saving/reloading the
authored extraction contract, not for iterating workflow execution groups.

## Compatibility

Legacy YAML with no authored metadata must continue to prepare, load, and
serialize as before. If the persisted payload is richer than the legacy
execution-only payload, legacy callers must still be able to call the existing
execution methods without receiving metadata keys as groups.

## Test Fixture Shape

Use a sanitized fixture modeled after the attached Get Choice YAML, not the full
customer file. It must preserve the same policy key families that were stripped
from the real compiled workflow:

```yaml
extraction_policy_version: v1

statement:
  slot: chunk-instruct
  final_value_aliases:
    demand_kw: demand
  fill_rules:
    statement_period_end: latest
  fields:
    account_number:
      prompt:
        attr_name: account_number
        description: Account number.

meters:
  slot: chunk-summary
  always_check_attrs: [meter_number]
  conflict_attrs: [meter_number]
  exclude_dict_attrs: [meter_decisions]
  passthrough_attrs:
    - meter_number
  remaining_attrs: [usage_value]
  required_attrs: [meter_number]
  not_required_service_types: [irrigation]
  equivalent_service_types:
    water: water
  partial_pair_attrs: [measurement_period_start_date, measurement_period_end_date]
  passthrough_pair_attrs: [meter_number, tariff]
  deregulation_status_values:
    delivery: delivery
    supply: supply
    full_service: full service
  fields:
    meter_number:
      prompt:
        attr_name: meter_number
        description: Meter number.

charges:
  slot: chunk-keys
  always_check_attrs: [charge_description_as_printed]
  match_attrs:
    - meter_number
  unique_attrs: [charge_description_as_printed]
  required_any_attrs:
    - charge_amount
  conflict_attrs: [charge_amount]
  exclude_dict_attrs: [charge_decisions]
  fields:
    charge_amount:
      prompt:
        attr_name: charge_amount
        description: Charge amount.
```

Add `_pseudo_groups` to one fixture variant so the same persisted-payload tests
cover workflow-only groups and final-only metadata.

The regression must also compare against the attached failure shape: a compiled
workflow whose `extract.statement`, `extract.meters`, and `extract.charges`
contain only `fields`/`prompt` is not sufficient.

## Risks

- If the persisted payload preserves metadata but is not accepted as a workflow
  `extract` payload, harness compile will look fixed while workflow create or
  execution regresses.
- If metadata is put into `workflow.extract` without a safe SDK parser, older
  readers can treat `extraction_policy_version` or other metadata keys as final
  groups.
- If the harness keeps writing sidecar-only metadata, Arcadia will still miss
  the metadata in live workflows.
- If the SDK changes `workflow_extract_dict()` semantics without a clear new
  method, existing callers may accidentally send authoring metadata to execution
  paths that expect group-shaped mappings only.
- If dict input is not supported, Arcadia can only test local YAML files and will
  still fail when reloading the deployed workflow API payload.
