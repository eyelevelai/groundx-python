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
