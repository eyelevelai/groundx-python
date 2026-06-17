import copy
import json
import typing

from groundx.extract import prepare_extraction_yaml
from groundx.extract.prompt.manager import PromptManager
from groundx.types.workflow_request import WorkflowRequest

from ._fixtures import SAMPLE_YAML_1, TestSource


TOP_LEVEL_METADATA_KEYS = {"extraction_policy_version"}
FINAL_GROUP_METADATA_KEYS = {
    "final_value_aliases",
    "fill_rules",
    "always_check_attrs",
    "match_attrs",
    "unique_attrs",
    "required_any_attrs",
    "conflict_attrs",
    "exclude_dict_attrs",
    "explanation_attrs",
    "passthrough_attrs",
    "remaining_attrs",
    "required_attrs",
    "not_required_service_types",
    "equivalent_service_types",
    "partial_pair_attrs",
    "passthrough_pair_attrs",
    "deregulation_status_values",
}
WORKFLOW_GROUP_METADATA_KEYS = {"slot"}


POLICY_YAML = """
extraction_policy_version: v1

statement:
  slot: chunk-instruct
  final_value_aliases:
    amount_due: total_due
  fill_rules:
    - source: provider_name
      target: /meters/provider_name
  explanation_attrs:
    - statement_explanation
  fields:
    account_number:
      prompt:
        description: Account number.
        identifiers:
          - Account Number
        instructions: Return the account number.
        type: str
    amount_due:
      prompt:
        description: Amount due.
        identifiers:
          - Amount Due
        instructions: Return the amount due.
        type: float
    provider_name:
      prompt:
        description: Provider name.
        identifiers:
          - Provider
        instructions: Return the provider name.
        type: str

meters:
  slot: chunk-summary
  always_check_attrs:
    - meter_number
  conflict_attrs:
    - meter_number
  exclude_dict_attrs:
    - meter_decisions
  explanation_attrs:
    - meter_explanation
  passthrough_attrs:
    - meter_number
  remaining_attrs:
    - usage_value
  required_attrs:
    - meter_number
  not_required_service_types:
    - irrigation
  equivalent_service_types:
    water: potable_water
  partial_pair_attrs:
    - measurement_period_start_date
    - measurement_period_end_date
  passthrough_pair_attrs:
    - meter_number
    - tariff
  deregulation_status_values:
    delivery: delivery
    supply: supply
    full_service: full service
  fields:
    meter_number:
      prompt:
        description: Meter number.
        identifiers:
          - Meter Number
        instructions: Return the meter number.
        type: str

charges:
  slot: chunk-keys
  always_check_attrs:
    - charge_description_as_printed
  match_attrs:
    - meter_number
  unique_attrs:
    - charge_description_as_printed
  required_any_attrs:
    - charge_amount
  conflict_attrs:
    - charge_amount
  exclude_dict_attrs:
    - charge_decisions
  explanation_attrs:
    - charge_explanation
  fields:
    charge_amount:
      prompt:
        description: Charge amount.
        identifiers:
          - Charge Amount
        instructions: Return the charge amount.
        type: float

_pseudo_groups:
  statement_identity:
    slot: chunk-keys
    fields:
      account_number:
        path: /statement/account_number
"""


def _prepare(raw: typing.Any):
    return prepare_extraction_yaml(
        raw,
        top_level_metadata_keys=TOP_LEVEL_METADATA_KEYS,
        final_group_metadata_keys=FINAL_GROUP_METADATA_KEYS,
        workflow_group_metadata_keys=WORKFLOW_GROUP_METADATA_KEYS,
    )


def test_persisted_workflow_extract_round_trips_authored_metadata() -> None:
    prepared = _prepare(POLICY_YAML)

    persisted = prepared.persisted_workflow_extract
    round_tripped = json.loads(json.dumps(persisted))
    reloaded = _prepare(round_tripped)

    assert reloaded.top_level_metadata == {"extraction_policy_version": "v1"}
    assert reloaded.final_group_metadata["statement"]["final_value_aliases"] == {
        "amount_due": "total_due"
    }
    assert reloaded.final_group_metadata["statement"]["explanation_attrs"] == [
        "statement_explanation"
    ]
    assert reloaded.final_group_metadata["meters"]["passthrough_attrs"] == [
        "meter_number"
    ]
    assert reloaded.final_group_metadata["meters"]["explanation_attrs"] == [
        "meter_explanation"
    ]
    assert reloaded.final_group_metadata["charges"]["match_attrs"] == ["meter_number"]
    assert reloaded.final_group_metadata["charges"]["explanation_attrs"] == [
        "charge_explanation"
    ]
    assert reloaded.workflow_group_metadata["statement_identity"] == {
        "slot": "chunk-keys"
    }
    assert reloaded.workflow_field_paths["statement_identity"] == {
        "account_number": "/statement/account_number"
    }


def test_prepare_extraction_yaml_accepts_mapping_without_mutating_it() -> None:
    prepared = _prepare(POLICY_YAML)
    persisted = prepared.persisted_workflow_extract
    caller_owned = copy.deepcopy(persisted)

    reloaded = _prepare(caller_owned)

    assert caller_owned == persisted
    assert reloaded.final_group_metadata == prepared.final_group_metadata
    assert reloaded.workflow_group_metadata == prepared.workflow_group_metadata


def test_persisted_workflow_extract_keeps_execution_groups_resolvable() -> None:
    source = TestSource(POLICY_YAML)
    manager = PromptManager(
        cache_source=source,
        config_source=source,
        top_level_metadata_keys=TOP_LEVEL_METADATA_KEYS,
        final_group_metadata_keys=FINAL_GROUP_METADATA_KEYS,
        workflow_group_metadata_keys=WORKFLOW_GROUP_METADATA_KEYS,
    )

    workflow_extract = manager.workflow_extract_dict()
    persisted = manager.persisted_workflow_extract_dict()
    request = WorkflowRequest(extract=persisted)

    assert request.extract == persisted
    assert set(workflow_extract).issubset(set(persisted))
    assert "statement_identity" in persisted
    assert "statement_identity" not in persisted["_groundx_persisted_extract"]
    assert "extraction_policy_version" in persisted["_groundx_persisted_extract"]


def test_legacy_yaml_persisted_extract_is_execution_shaped() -> None:
    source = TestSource(SAMPLE_YAML_1)
    manager = PromptManager(cache_source=source, config_source=source)

    persisted = manager.persisted_workflow_extract_dict()

    assert persisted == manager.workflow_extract_dict()
    assert "_groundx_persisted_extract" not in persisted
    assert _prepare(persisted).workflow_field_paths == {
        "statement": {"statement_date": "/statement/statement_date"},
        "meters": {
            "meter_number": "/meters/meter_number",
            "service_address": "/meters/service_address",
        },
    }


# ---------------------------------------------------------------------------
# AGE-148: custom-step keys
# ---------------------------------------------------------------------------

CUSTOM_STEP_YAML = """
_template:
  chunk-instruct: my-instruct-template
_custom_steps:
  - name: adp_chunk_01
    level: chunk
    kind: instruct
  - name: adp_section_01
    level: section
    kind: summary
_output_routes:
  - step: adp_chunk_01
    field: plan_type
_leaf_fields:
  - step: adp_chunk_01
    path: /adp_chunk/plan_type
statement:
  fields:
    account_number:
      prompt:
        identifiers:
          - Account Number
        instructions: Return the account number.
        type: str
"""


def test_custom_step_keys_populate_prepared_fields() -> None:
    """Task 1.3(a): YAML with all four custom-step keys → fields populated."""
    prepared = prepare_extraction_yaml(CUSTOM_STEP_YAML)

    assert prepared.custom_template == {"chunk-instruct": "my-instruct-template"}
    assert prepared.custom_steps == [
        {"name": "adp_chunk_01", "level": "chunk", "kind": "instruct"},
        {"name": "adp_section_01", "level": "section", "kind": "summary"},
    ]
    assert prepared.output_routes == [{"step": "adp_chunk_01", "field": "plan_type"}]
    assert prepared.leaf_fields == [
        {"step": "adp_chunk_01", "path": "/adp_chunk/plan_type"}
    ]


def test_yaml_without_custom_step_keys_produces_empty_fields() -> None:
    """Task 1.3(b): YAML without custom-step keys → fields empty/None."""
    prepared = prepare_extraction_yaml(SAMPLE_YAML_1)

    assert prepared.custom_template is None
    assert prepared.custom_steps == []
    assert prepared.output_routes == []
    assert prepared.leaf_fields == []


def test_custom_step_keys_do_not_affect_existing_group_behavior() -> None:
    """Task 1.3(c): existing group / workflow-group behavior unchanged."""
    prepared_without = prepare_extraction_yaml(SAMPLE_YAML_1)
    prepared_with = prepare_extraction_yaml(CUSTOM_STEP_YAML)

    # groups in CUSTOM_STEP_YAML are just 'statement'
    assert "statement" in prepared_with.groups
    # groups in SAMPLE_YAML_1 are statement + meters
    assert list(prepared_without.groups.keys()) == ["statement", "meters"]

    # workflow_field_paths for common group is unchanged
    assert prepared_without.workflow_field_paths["statement"] == {
        "statement_date": "/statement/statement_date"
    }
    assert prepared_with.workflow_field_paths["statement"] == {
        "account_number": "/statement/account_number"
    }


def test_custom_step_keys_round_trip_through_persisted_extract() -> None:
    """Custom-step authoring metadata survives JSON round-trip."""
    prepared = prepare_extraction_yaml(CUSTOM_STEP_YAML)

    persisted = prepared.persisted_workflow_extract
    round_tripped = json.loads(json.dumps(persisted))
    reloaded = prepare_extraction_yaml(round_tripped)

    assert reloaded.custom_template == prepared.custom_template
    assert reloaded.custom_steps == prepared.custom_steps
    assert reloaded.output_routes == prepared.output_routes
    assert reloaded.leaf_fields == prepared.leaf_fields


def test_custom_steps_not_exposed_as_workflow_groups() -> None:
    """_custom_steps and sibling keys must NOT appear as workflow groups."""
    prepared = prepare_extraction_yaml(CUSTOM_STEP_YAML)

    for key in ("_template", "_custom_steps", "_output_routes", "_leaf_fields"):
        assert key not in prepared.workflow_groups, (
            f"{key} must not appear in workflow_groups"
        )


# ---------------------------------------------------------------------------
# AGE-148: _validate_custom_step fail-fast validation
# ---------------------------------------------------------------------------


def test_invalid_step_name_with_space_raises_value_error() -> None:
    """Task 3.1(a): name with a space raises ValueError."""
    yaml_text = """
_custom_steps:
  - name: "bad name"
    level: chunk
    kind: instruct
statement:
  fields:
    x:
      prompt:
        instructions: x
        type: str
"""
    try:
        prepare_extraction_yaml(yaml_text)
        raise AssertionError("Expected ValueError was not raised")
    except ValueError as exc:
        assert "bad name" in str(exc) or "name" in str(exc)


def test_invalid_level_raises_value_error() -> None:
    """Task 3.1(b): level: 'paragraph' raises ValueError."""
    yaml_text = """
_custom_steps:
  - name: adp_chunk_01
    level: paragraph
    kind: instruct
statement:
  fields:
    x:
      prompt:
        instructions: x
        type: str
"""
    try:
        prepare_extraction_yaml(yaml_text)
        raise AssertionError("Expected ValueError was not raised")
    except ValueError as exc:
        assert "paragraph" in str(exc) or "level" in str(exc)


def test_invalid_kind_raises_value_error() -> None:
    """Task 3.1(c): kind: 'embed' raises ValueError."""
    yaml_text = """
_custom_steps:
  - name: adp_chunk_01
    level: chunk
    kind: embed
statement:
  fields:
    x:
      prompt:
        instructions: x
        type: str
"""
    try:
        prepare_extraction_yaml(yaml_text)
        raise AssertionError("Expected ValueError was not raised")
    except ValueError as exc:
        assert "embed" in str(exc) or "kind" in str(exc)


def test_valid_custom_step_passes_validation() -> None:
    """Task 3.1(d): valid step {name, level, kind} passes validation."""
    yaml_text = """
_custom_steps:
  - name: adp_chunk_01
    level: chunk
    kind: instruct
statement:
  fields:
    x:
      prompt:
        instructions: x
        type: str
"""
    prepared = prepare_extraction_yaml(yaml_text)
    assert prepared.custom_steps == [
        {"name": "adp_chunk_01", "level": "chunk", "kind": "instruct"}
    ]


# ---------------------------------------------------------------------------
# AGE-148: backward-compat regression test (task 7.2)
# ---------------------------------------------------------------------------


def test_legacy_yaml_produces_same_groups_and_field_paths() -> None:
    """Task 7.2: legacy YAML (no custom-step keys) → same groups/paths/extract_dict."""
    prepared = prepare_extraction_yaml(SAMPLE_YAML_1)

    assert list(prepared.groups.keys()) == ["statement", "meters"]
    assert prepared.workflow_field_paths == {
        "statement": {"statement_date": "/statement/statement_date"},
        "meters": {
            "meter_number": "/meters/meter_number",
            "service_address": "/meters/service_address",
        },
    }

    # workflow_extract_dict comes from PromptManager; do a light check via persisted
    source = TestSource(SAMPLE_YAML_1)
    from groundx.extract.prompt.manager import PromptManager

    manager = PromptManager(cache_source=source, config_source=source)
    wfe = manager.workflow_extract_dict()
    assert "statement" in wfe
    assert "meters" in wfe
    # custom-step keys are absent
    assert prepared.custom_template is None
    assert prepared.custom_steps == []
    assert prepared.output_routes == []
    assert prepared.leaf_fields == []
