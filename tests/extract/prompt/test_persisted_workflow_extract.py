import copy
import json
import typing

import pytest

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


def _custom_workflow_metadata() -> typing.Dict[str, typing.Any]:
    return {
        "metadata_version": 1,
        "template": {
            "BILLING_HINT": "Prefer values from the charge table.",
        },
        "custom_steps": [
            {
                "name": "line_item_labels",
                "level": "chunk",
                "kind": "keys",
                "required_template_keys": ["BILLING_HINT"],
            }
        ],
        "output_routes": [
            {
                "workflow_group": "line_items",
                "workflow_field": "description",
                "final_path": "/line_items/*/description",
                "step_name": "line_item_labels",
                "level": "chunk",
                "output_map": "customChunkOutputs",
                "output_key": "label",
                "readback_path": (
                    "/chunks/*/customChunkOutputs/line_item_labels/label"
                ),
            }
        ],
        "leaf_fields": [
            {
                "final_path": "/line_items/*/description",
                "workflow_group": "line_items",
                "workflow_field": "description",
                "step_name": "line_item_labels",
                "level": "chunk",
                "output_key": "label",
                "field_type": "str",
                "is_repeated": True,
                "repetition_scope": "/line_items/*",
            }
        ],
        "field_counts": {"line_item_labels": 1},
    }


def _persisted_custom_workflow_extract() -> typing.Dict[str, typing.Any]:
    return {
        "line_items": {
            "fields": {
                "description": {
                    "prompt": {
                        "identifiers": ["Description"],
                        "instructions": "Return the line item description.",
                        "type": "str",
                    }
                }
            }
        },
        "workflow": _custom_workflow_metadata(),
    }


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


def test_persisted_custom_workflow_extract_round_trips_routes_and_leaf_fields() -> None:
    persisted = _persisted_custom_workflow_extract()
    round_tripped = json.loads(json.dumps(persisted))

    reloaded = prepare_extraction_yaml(round_tripped)
    workflow = reloaded.persisted_workflow_extract["workflow"]

    assert workflow["metadata_version"] == 1
    assert workflow["custom_steps"] == persisted["workflow"]["custom_steps"]
    assert workflow["output_routes"] == persisted["workflow"]["output_routes"]
    assert workflow["leaf_fields"] == persisted["workflow"]["leaf_fields"]
    assert workflow["leaf_fields"][0]["final_path"] == "/line_items/*/description"
    assert workflow["leaf_fields"][0]["repetition_scope"] == "/line_items/*"
    assert reloaded.workflow_field_paths["line_items"]["description"] == (
        "/line_items/*/description"
    )


def test_persisted_custom_workflow_extract_rejects_unknown_version() -> None:
    persisted = _persisted_custom_workflow_extract()
    persisted["workflow"]["metadata_version"] = 2

    with pytest.raises(ValueError, match="metadata_version"):
        prepare_extraction_yaml(persisted)


def test_persisted_custom_workflow_extract_rejects_missing_version() -> None:
    persisted = _persisted_custom_workflow_extract()
    del persisted["workflow"]["metadata_version"]

    with pytest.raises(ValueError, match="metadata_version"):
        prepare_extraction_yaml(persisted)


def test_persisted_custom_workflow_extract_rejects_route_leaf_mismatch() -> None:
    persisted = _persisted_custom_workflow_extract()
    persisted["workflow"]["leaf_fields"][0]["final_path"] = "/line_items/*/amount"

    with pytest.raises(ValueError, match="route.*leaf|leaf.*route"):
        prepare_extraction_yaml(persisted)


def test_persisted_custom_workflow_extract_rejects_field_count_mismatch() -> None:
    persisted = _persisted_custom_workflow_extract()
    persisted["workflow"]["field_counts"] = {"line_item_labels": 2}

    with pytest.raises(ValueError, match="field_counts"):
        prepare_extraction_yaml(persisted)


def test_persisted_custom_workflow_extract_hash_is_deterministic() -> None:
    first = _persisted_custom_workflow_extract()
    second = _persisted_custom_workflow_extract()
    second["workflow"]["template"] = {
        "BILLING_HINT": "Template values are ignored by hash",
    }
    second["workflow"]["custom_steps"][0]["required_template_keys"] = list(
        reversed(second["workflow"]["custom_steps"][0]["required_template_keys"])
    )
    second["workflow"]["output_routes"] = list(
        reversed(second["workflow"]["output_routes"])
    )
    second["workflow"]["leaf_fields"] = list(reversed(second["workflow"]["leaf_fields"]))

    first_hash = prepare_extraction_yaml(first).persisted_workflow_extract["workflow"][
        "schema_hash"
    ]
    second_hash = prepare_extraction_yaml(second).persisted_workflow_extract["workflow"][
        "schema_hash"
    ]

    assert first_hash == second_hash
    assert len(first_hash) == 64
