import copy
import json
import typing

import pytest
from ._fixtures import SAMPLE_YAML_1, TestSource

from groundx.extract import prepare_extraction_yaml
from groundx.extract.prompt.manager import PromptManager
from groundx.types.workflow_request import WorkflowRequest

TOP_LEVEL_METADATA_KEYS = {"extraction_policy_version"}
FINAL_GROUP_METADATA_KEYS = {
    "fill_rules",
    "always_check_attrs",
    "match_attrs",
    "unique_attrs",
    "identity_match",
    "passthrough_transform",
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
WORKFLOW_GROUP_METADATA_KEYS = {"workflow_step"}


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
                "readback_path": ("/chunks/*/customChunkOutputs/line_item_labels/label"),
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
  workflow_step: chunk-instruct
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
  workflow_step: chunk-summary
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
  workflow_step: chunk-keys
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
    charge_description_as_printed:
      prompt:
        description: Printed charge description.
        identifiers:
          - Charge Description
        instructions: Return the printed charge description.
        type: str
    charge_amount:
      prompt:
        description: Charge amount.
        identifiers:
          - Charge Amount
        instructions: Return the charge amount.
        type: float

_pseudo_groups:
  statement_identity:
    workflow_step: chunk-keys
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
    assert reloaded.final_group_metadata["statement"]["explanation_attrs"] == ["statement_explanation"]
    assert reloaded.final_group_metadata["meters"]["passthrough_attrs"] == ["meter_number"]
    assert reloaded.final_group_metadata["meters"]["explanation_attrs"] == ["meter_explanation"]
    assert reloaded.final_group_metadata["charges"]["match_attrs"] == ["meter_number"]
    assert reloaded.final_group_metadata["charges"]["explanation_attrs"] == ["charge_explanation"]
    assert reloaded.workflow_group_metadata["statement_identity"] == {"workflow_step": "chunk-keys"}
    assert reloaded.workflow_field_paths["statement_identity"] == {"account_number": "/statement/account_number"}


def test_object_array_policy_metadata_round_trips_without_rewriting() -> None:
    raw = """
extraction_policy_version: v1

generic_parents:
  unique_attrs:
    - object_code
    - market_state
    - primary_company
    - alternate_company
  identity_match:
    threshold_attrs:
      - market_state
      - primary_company
      - alternate_company
    activate_threshold_at: 2
    minimum_threshold_matches: 3
    group_attrs:
      - object_code
      - market_state
    sort_attrs:
      - object_code
    equal_value_shortcuts:
      market_state:
        - combined
  passthrough_transform:
    status_attr: market_state
    provider_attr: primary_company
    passthrough_provider_attr: alternate_company
    clear_attrs:
      - alternate_company
  fields:
    object_code:
      prompt: {instructions: Return the object code., type: str}
    market_state:
      prompt: {instructions: Return the market state., type: str}
    primary_company:
      prompt: {instructions: Return the primary company., type: str}
    alternate_company:
      prompt: {instructions: Return the alternate company., type: str}
"""

    prepared = _prepare(raw)
    persisted = json.loads(json.dumps(prepared.persisted_workflow_extract))
    reloaded = _prepare(persisted)

    expected = {
        "unique_attrs": [
            "object_code",
            "market_state",
            "primary_company",
            "alternate_company",
        ],
        "identity_match": {
            "threshold_attrs": [
                "market_state",
                "primary_company",
                "alternate_company",
            ],
            "activate_threshold_at": 2,
            "minimum_threshold_matches": 3,
            "group_attrs": ["object_code", "market_state"],
            "sort_attrs": ["object_code"],
            "equal_value_shortcuts": {"market_state": ["combined"]},
        },
        "passthrough_transform": {
            "status_attr": "market_state",
            "provider_attr": "primary_company",
            "passthrough_provider_attr": "alternate_company",
            "clear_attrs": ["alternate_company"],
        },
    }
    assert prepared.final_group_metadata["generic_parents"] == expected
    assert reloaded.final_group_metadata["generic_parents"] == expected
    assert persisted["_groundx_persisted_extract"]["generic_parents"] == expected | {
        "fields": prepared.groups["generic_parents"]["fields"]
    }


def test_object_array_policy_accepts_supplemental_threshold_attrs() -> None:
    raw = """
extraction_policy_version: v1

generic_objects:
  unique_attrs: [object_code, object_kind, object_status]
  identity_match:
    exact_attrs: [object_code, object_kind, object_status]
    threshold_attrs: [object_status, primary_party, alternate_party, source_party]
    activate_threshold_at: 2
    minimum_threshold_matches: 3
    group_attrs: [object_code, object_kind, object_status]
    sort_attrs: [object_code]
    equal_value_shortcuts:
      object_status: [combined]
  fields:
    object_code:
      prompt: {instructions: Return the object code., type: str}
    object_kind:
      prompt: {instructions: Return the object kind., type: str}
    object_status:
      prompt: {instructions: Return the object status., type: str}
    primary_party:
      prompt: {instructions: Return the primary party., type: str}
    alternate_party:
      prompt: {instructions: Return the alternate party., type: str}
    source_party:
      prompt: {instructions: Return the source party., type: str}
"""

    prepared = _prepare(raw)
    reloaded = _prepare(json.loads(json.dumps(prepared.persisted_workflow_extract)))

    expected_thresholds = [
        "object_status",
        "primary_party",
        "alternate_party",
        "source_party",
    ]
    assert prepared.final_group_metadata["generic_objects"]["identity_match"][
        "threshold_attrs"
    ] == expected_thresholds
    assert reloaded.final_group_metadata["generic_objects"]["identity_match"][
        "threshold_attrs"
    ] == expected_thresholds


@pytest.mark.parametrize(
    ("metadata", "message"),
    [
        (
            "identity_match: {threshold_attrs: [missing_attr]}",
            "identity_match attributes must exist in group [generic_rows]",
        ),
        (
            "identity_match: {exact_attrs: [secondary_code]}",
            "identity_match attributes must also be declared in unique_attrs",
        ),
        (
            "identity_match: {group_attrs: [secondary_code]}",
            "identity_match attributes must also be declared in unique_attrs",
        ),
        (
            "identity_match: {sort_attrs: [secondary_code]}",
            "identity_match attributes must also be declared in unique_attrs",
        ),
        (
            "identity_match: {threshold_attrs: [object_code], activate_threshold_at: -1}",
            "activate_threshold_at must be a non-negative integer",
        ),
        (
            "identity_match: {threshold_attrs: [object_code], activate_threshold_at: true}",
            "activate_threshold_at must be a non-negative integer",
        ),
        (
            "identity_match: {threshold_attrs: [object_code], minimum_threshold_matches: 2}",
            "minimum_threshold_matches cannot exceed threshold_attrs",
        ),
        (
            "identity_match: {threshold_attrs: [object_code], minimum_threshold_matches: true}",
            "minimum_threshold_matches must be a non-negative integer",
        ),
        (
            "identity_match: {equal_value_shortcuts: {object_code: [1]}}",
            "equal_value_shortcuts values must be lists of strings",
        ),
        (
            "passthrough_transform: {status_attr: object_code, provider_attr: missing_attr, passthrough_provider_attr: secondary_code}",
            "passthrough_transform attributes must exist in group [generic_rows]",
        ),
    ],
)
def test_object_array_policy_metadata_rejects_invalid_contracts(
    metadata: str,
    message: str,
) -> None:
    raw = f"""
extraction_policy_version: v1

generic_rows:
  unique_attrs: [object_code]
  {metadata}
  fields:
    object_code:
      prompt: {{instructions: Return the object code., type: str}}
    secondary_code:
      prompt: {{instructions: Return the secondary code., type: str}}
"""

    with pytest.raises(ValueError, match=message.replace("[", r"\[").replace("]", r"\]")):
        _prepare(raw)


def test_object_array_policy_rejects_unknown_unique_attr() -> None:
    raw = """
extraction_policy_version: v1

generic_rows:
  unique_attrs: [missing_attr]
  fields:
    object_code:
      prompt: {instructions: Return the object code., type: str}
"""

    with pytest.raises(
        ValueError,
        match=r"unique_attrs fields must exist in group \[generic_rows\]",
    ):
        _prepare(raw)


def test_persisted_canonical_v1_rejects_output_aliases() -> None:
    persisted = copy.deepcopy(_prepare(POLICY_YAML).persisted_workflow_extract)
    persisted["_groundx_persisted_extract"]["statement"]["final_value_aliases"] = {"amount_due": "total_due"}

    with pytest.raises(
        ValueError,
        match="final_value_aliases.*not supported.*canonical v1",
    ):
        _prepare(persisted)


def test_versionless_authored_yaml_rejects_output_aliases() -> None:
    raw = """
statement:
  final_value_aliases:
    statement_period_start_date: measurement_period_start_date
  fields:
    statement_period_start_date:
      prompt:
        instructions: Return the statement period start date.
        type: str
"""

    with pytest.raises(
        ValueError,
        match="final_value_aliases.*extraction_policy_version: v1",
    ):
        prepare_extraction_yaml(raw)


def test_persisted_workflow_extract_round_trips_pseudo_group_metadata() -> None:
    raw = """
extraction_policy_version: v1

statement:
  role: statement
  fields:
    account_number:
      prompt:
        instructions: Return the account number.
        type: str

_pseudo_groups:
  statement_identity:
    role: statement
    workflow_step: chunk-keys
    fields:
      account_number:
        path: /statement/account_number
"""

    prepared = prepare_extraction_yaml(
        raw,
        final_group_metadata_keys={"role"},
        workflow_group_metadata_keys={"workflow_step"},
        pseudo_group_metadata_keys={"role"},
    )
    reloaded = prepare_extraction_yaml(
        json.loads(json.dumps(prepared.persisted_workflow_extract)),
        final_group_metadata_keys={"role"},
        workflow_group_metadata_keys={"workflow_step"},
        pseudo_group_metadata_keys={"role"},
    )

    assert prepared.final_group_metadata["statement"] == {"role": "statement"}
    assert prepared.workflow_group_metadata["statement_identity"] == {
        "role": "statement",
        "workflow_step": "chunk-keys",
    }
    assert reloaded.final_group_metadata == prepared.final_group_metadata
    assert reloaded.workflow_group_metadata == prepared.workflow_group_metadata


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
    assert reloaded.workflow_field_paths["line_items"]["description"] == ("/line_items/*/description")


def test_persisted_relationship_round_trips_first_stable_match_strategy() -> None:
    persisted = _persisted_custom_workflow_extract()
    persisted["workflow"]["output_relationships"] = [
        {
            "parent_group": "parents",
            "child_group": "children",
            "parent_output_field": "children",
            "match_attrs": ["record_key"],
            "unmatched_child_group": "children",
            "multiple_match_strategy": "first_stable",
        }
    ]

    reloaded = prepare_extraction_yaml(persisted)

    assert reloaded.persisted_workflow_extract["workflow"]["output_relationships"] == [
        {
            "parent_group": "parents",
            "child_group": "children",
            "parent_output_field": "children",
            "match_attrs": ["record_key"],
            "unmatched_child_group": "children",
            "multiple_match_strategy": "first_stable",
        }
    ]


def test_authored_output_relationships_persist_in_workflow_metadata() -> None:
    raw = """
extraction_policy_version: v1
workflow:
  custom_steps:
    - name: account_rows
      level: chunk
      kind: summary
    - name: transaction_rows
      level: chunk
      kind: keys
  output_relationships:
    - parent_group: accounts
      child_group: transactions
      parent_output_field: transactions
      match_attrs: [account_id]
      unmatched_child_group: unmatched_transactions

accounts:
  workflow_step: account_rows
  fields:
    account_id:
      workflow_output_key: account_id
      prompt:
        instructions: Return the account id.
        type: str

transactions:
  workflow_step: transaction_rows
  fields:
    account_id:
      workflow_output_key: account_id
      prompt:
        instructions: Return the account id.
        type: str
    amount:
      workflow_output_key: amount
      prompt:
        instructions: Return the transaction amount.
        type: float
"""

    prepared = prepare_extraction_yaml(raw)
    relationship = prepared.persisted_workflow_extract["workflow"]["output_relationships"][0]

    assert relationship == {
        "parent_group": "accounts",
        "child_group": "transactions",
        "parent_output_field": "transactions",
        "match_attrs": ["account_id"],
        "unmatched_child_group": "unmatched_transactions",
    }


def test_final_group_relationship_metadata_converts_when_parent_is_explicit() -> None:
    raw = """
extraction_policy_version: v1
workflow:
  custom_steps:
    - name: account_rows
      level: chunk
      kind: summary
    - name: transaction_rows
      level: chunk
      kind: keys

accounts:
  workflow_step: account_rows
  fields:
    account_id:
      workflow_output_key: account_id
      prompt:
        instructions: Return the account id.
        type: str

transactions:
  workflow_step: transaction_rows
  match_attrs: [account_id]
  passthrough:
    from: accounts
    fields: [billing_period]
  fields:
    account_id:
      workflow_output_key: account_id
      prompt:
        instructions: Return the account id.
        type: str
    amount:
      workflow_output_key: amount
      prompt:
        instructions: Return the transaction amount.
        type: float
"""

    prepared = prepare_extraction_yaml(raw)

    assert prepared.persisted_workflow_extract["workflow"]["output_relationships"] == [
        {
            "parent_group": "accounts",
            "child_group": "transactions",
            "parent_output_field": "transactions",
            "match_attrs": ["account_id"],
            "unmatched_child_group": "transactions",
        }
    ]


def test_final_group_match_attrs_without_parent_does_not_guess_relationship() -> None:
    raw = """
extraction_policy_version: v1
workflow:
  custom_steps:
    - name: transaction_rows
      level: chunk
      kind: keys

transactions:
  workflow_step: transaction_rows
  match_attrs: [account_id]
  fields:
    account_id:
      workflow_output_key: account_id
      prompt:
        instructions: Return the account id.
        type: str
"""

    prepared = prepare_extraction_yaml(raw)

    assert "output_relationships" not in prepared.persisted_workflow_extract["workflow"]


def test_final_group_passthrough_can_name_relationship_outputs() -> None:
    raw = """
extraction_policy_version: v1
workflow:
  custom_steps:
    - {name: parent_rows, level: chunk, kind: keys}
    - {name: child_rows, level: chunk, kind: keys}
parents:
  workflow_step: parent_rows
  fields:
    record_key:
      workflow_output_key: record_key
      prompt: {instructions: Return the key, type: str}
children:
  workflow_step: child_rows
  match_attrs: [record_key]
  passthrough:
    from: parents
    parent_output_field: nested_children
    unmatched_child_group: unassigned_children
  fields:
    record_key:
      workflow_output_key: record_key
      prompt: {instructions: Return the key, type: str}
"""

    prepared = prepare_extraction_yaml(raw)

    assert prepared.persisted_workflow_extract["workflow"]["output_relationships"] == [
        {
            "parent_group": "parents",
            "child_group": "children",
            "parent_output_field": "nested_children",
            "match_attrs": ["record_key"],
            "unmatched_child_group": "unassigned_children",
        }
    ]


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
    second["workflow"]["output_routes"] = list(reversed(second["workflow"]["output_routes"]))
    second["workflow"]["leaf_fields"] = list(reversed(second["workflow"]["leaf_fields"]))

    first_hash = prepare_extraction_yaml(first).persisted_workflow_extract["workflow"]["schema_hash"]
    second_hash = prepare_extraction_yaml(second).persisted_workflow_extract["workflow"]["schema_hash"]

    assert first_hash == second_hash
    assert len(first_hash) == 64


def test_relationship_match_strategy_changes_schema_hash() -> None:
    first = _persisted_custom_workflow_extract()
    second = copy.deepcopy(first)
    relationship = {
        "parent_group": "parents",
        "child_group": "children",
        "parent_output_field": "children",
        "match_attrs": ["record_key"],
        "unmatched_child_group": "children",
    }
    first["workflow"]["output_relationships"] = [relationship]
    second["workflow"]["output_relationships"] = [
        {**relationship, "multiple_match_strategy": "first_stable"}
    ]

    first_hash = prepare_extraction_yaml(first).persisted_workflow_extract["workflow"]["schema_hash"]
    second_hash = prepare_extraction_yaml(second).persisted_workflow_extract["workflow"]["schema_hash"]

    assert first_hash != second_hash


def test_relationship_match_attr_order_does_not_change_schema_hash() -> None:
    first = _persisted_custom_workflow_extract()
    second = copy.deepcopy(first)
    relationship = {
        "parent_group": "parents",
        "child_group": "children",
        "parent_output_field": "children",
        "match_attrs": ["record_key", "category"],
        "unmatched_child_group": "children",
    }
    first["workflow"]["output_relationships"] = [relationship]
    second["workflow"]["output_relationships"] = [
        {**relationship, "match_attrs": list(reversed(relationship["match_attrs"]))}
    ]

    first_hash = prepare_extraction_yaml(first).persisted_workflow_extract["workflow"]["schema_hash"]
    second_hash = prepare_extraction_yaml(second).persisted_workflow_extract["workflow"]["schema_hash"]

    assert first_hash == second_hash


def test_exact_identity_attrs_change_schema_hash() -> None:
    first = _persisted_custom_workflow_extract()
    first["line_items"]["unique_attrs"] = ["description"]
    second = copy.deepcopy(first)
    second["line_items"]["identity_match"] = {"exact_attrs": ["description"]}

    first_prepared = prepare_extraction_yaml(first)
    second_prepared = prepare_extraction_yaml(second)
    first_hash = first_prepared.persisted_workflow_extract["workflow"]["schema_hash"]
    second_hash = second_prepared.persisted_workflow_extract["workflow"]["schema_hash"]

    assert first_hash != second_hash
    assert second_prepared.persisted_workflow_extract["_groundx_persisted_extract"][
        "line_items"
    ]["identity_match"] == {"exact_attrs": ["description"]}


def test_explicit_empty_exact_identity_attrs_change_schema_hash() -> None:
    missing = _persisted_custom_workflow_extract()
    missing["line_items"]["unique_attrs"] = ["description"]
    explicit_empty = copy.deepcopy(missing)
    explicit_empty["line_items"]["identity_match"] = {"exact_attrs": []}

    missing_hash = prepare_extraction_yaml(missing).persisted_workflow_extract[
        "workflow"
    ]["schema_hash"]
    explicit_empty_hash = prepare_extraction_yaml(
        explicit_empty
    ).persisted_workflow_extract["workflow"]["schema_hash"]

    assert missing_hash != explicit_empty_hash
