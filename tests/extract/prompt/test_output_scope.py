import pytest

from groundx.extract import FinalFieldPath, prepare_extraction_yaml


def _workflow_yaml(*groups: str, agent_chain: bool = False) -> str:
    lines = [
        "extraction_policy_version: v1",
        "",
        "workflow:",
        "  custom_steps:",
        "    - name: scalar_step",
        "      level: chunk",
        "      kind: instruct",
        "    - name: repeated_step",
        "      level: chunk",
        "      kind: keys",
    ]
    if agent_chain:
        lines.extend(
            [
                "  agent_chain:",
                "    - parallel:",
                "        - group: statement_fields",
                "          chain: [reconcile_statement, qa_statement, save_statement]",
                "        - group: grouped_statement_fields",
                "          chain: [reconcile_statement, qa_statement, save_statement]",
            ]
        )
    return "\n".join([*lines, *groups])


def test_prepare_extraction_yaml_uses_only_output_scope_for_root_placement() -> None:
    prepared = prepare_extraction_yaml(
        _workflow_yaml(
            """
statement_fields:
  role: statement
  workflow_step: scalar_step
  output_scope: document_root
  fill_rules:
    - source: account_number
      target: account_number
  fields:
    account:
      fields:
        number:
          workflow_output_key: account_number
          prompt:
            instructions: Return the account number.
            type: str

grouped_statement_fields:
  role: statement
  workflow_step: scalar_step
  fill_rules:
    - source: total
      target: total
  fields:
    totals:
      fields:
        amount:
          workflow_output_key: total
          prompt:
            instructions: Return the total.
            type: str
""",
            agent_chain=True,
        )
    )

    routes = {
        route["workflow_group"]: route["final_path"]
        for route in prepared.persisted_workflow_extract["workflow"]["output_routes"]
    }
    assert routes == {
        "statement_fields": "/account/number",
        "grouped_statement_fields": "/grouped_statement_fields/totals/amount",
    }
    assert prepared.workflow_group_metadata["statement_fields"] == {
        "workflow_step": "scalar_step",
        "output_scope": "document_root",
    }
    assert (
        prepared.persisted_workflow_extract["_groundx_persisted_extract"]["statement_fields"]["output_scope"]
        == "document_root"
    )


def test_prepare_extraction_yaml_rejects_explicit_grouped_scope() -> None:
    raw = _workflow_yaml(
        """
statement_fields:
  workflow_step: scalar_step
  output_scope: grouped
  fields:
    account_number:
      workflow_output_key: account_number
      prompt:
        instructions: Return the account number.
        type: str
"""
    )

    with pytest.raises(ValueError, match="unsupported output_scope"):
        prepare_extraction_yaml(raw)


def test_prepare_extraction_yaml_rejects_authored_v1_output_aliases() -> None:
    raw = _workflow_yaml(
        """
statement_fields:
  workflow_step: scalar_step
  final_value_aliases:
    account_number: renamed_account_number
  fields:
    account_number:
      workflow_output_key: account_number
      prompt:
        instructions: Return the account number.
        type: str
"""
    )

    with pytest.raises(
        ValueError,
        match="final_value_aliases.*not supported.*authored v1",
    ):
        prepare_extraction_yaml(raw)


@pytest.mark.parametrize("scope", ["root", "document", "DOCUMENT_ROOT"])
def test_prepare_extraction_yaml_rejects_unknown_output_scope(scope: str) -> None:
    raw = _workflow_yaml(
        f"""
statement_fields:
  workflow_step: scalar_step
  output_scope: {scope}
  fields:
    account_number:
      workflow_output_key: account_number
      prompt:
        instructions: Return the account number.
        type: str
"""
    )

    with pytest.raises(ValueError, match="unsupported output_scope"):
        prepare_extraction_yaml(raw)


def test_prepare_extraction_yaml_rejects_document_root_repeating_group() -> None:
    raw = _workflow_yaml(
        """
statement_fields:
  workflow_step: repeated_step
  output_scope: document_root
  fields:
    account_number:
      workflow_output_key: account_number
      prompt:
        instructions: Return each account number.
        type: str
"""
    )

    with pytest.raises(ValueError, match="repeating group.*document_root"):
        prepare_extraction_yaml(raw)


def test_prepare_extraction_yaml_compiles_complete_repeated_nested_path() -> None:
    prepared = prepare_extraction_yaml(
        _workflow_yaml(
            """
line_items:
  workflow_step: repeated_step
  fields:
    details:
      fields:
        description:
          workflow_output_key: description
          prompt:
            instructions: Return each description.
            type: str
"""
        )
    )

    route = prepared.persisted_workflow_extract["workflow"]["output_routes"][0]
    leaf = prepared.persisted_workflow_extract["workflow"]["leaf_fields"][0]
    assert route["final_path"] == "/line_items/*/details/description"
    assert leaf["final_path"] == "/line_items/*/details/description"
    assert leaf["is_repeated"] is True
    assert leaf["repetition_scope"] == "item"


def test_prepare_extraction_yaml_emits_api_repetition_scope_enum() -> None:
    prepared = prepare_extraction_yaml(
        _workflow_yaml(
            """
invoice:
  workflow_step: scalar_step
  fields:
    account_number:
      workflow_output_key: account_number
      prompt:
        instructions: Return the account number.
        type: str

line_items:
  workflow_step: repeated_step
  fields:
    description:
      workflow_output_key: description
      prompt:
        instructions: Return each description.
        type: str
"""
        )
    )

    leaves = prepared.persisted_workflow_extract["workflow"]["leaf_fields"]
    scopes = {leaf["workflow_group"]: leaf["repetition_scope"] for leaf in leaves}
    assert scopes == {"invoice": "none", "line_items": "item"}


# Shared compiler-parity golden: the same YAML is compiled by the Studio
# Harness compile_workflow.py tests. A divergence between the two compilers on
# this schema must fail a test the day it is introduced.
_PARITY_GOLDEN_YAML = """\
extraction_policy_version: v1
workflow:
  custom_steps:
    - name: claim_rows
      level: chunk
      kind: keys
  agent_chain:
    - parallel:
        - group: claims
          chain: [reconcile_charges, save_charges]
claims:
  workflow_step: claim_rows
  role: charges
  fields:
    claim_number:
      workflow_output_key: claim_number
      prompt:
        description: claim number
        type: str
        identifiers: ["Claim"]
        instructions: Return the claim number.
"""


def test_parity_golden_repeated_group_emits_enum_scope() -> None:
    prepared = prepare_extraction_yaml(_PARITY_GOLDEN_YAML)

    leaves = prepared.persisted_workflow_extract["workflow"]["leaf_fields"]
    assert [leaf["repetition_scope"] for leaf in leaves] == ["item"]
    assert leaves[0]["final_path"] == "/claims/*/claim_number"
    assert leaves[0]["is_repeated"] is True


def test_final_field_path_accepts_complete_destination_trees() -> None:
    for pointer in (
        "/field",
        "/object/field",
        "/group/object/field",
        "/group/*/object/field",
    ):
        assert FinalFieldPath.parse(pointer).to_pointer() == pointer


def test_prepare_extraction_yaml_rejects_ancestor_destination_collision() -> None:
    raw = _workflow_yaml(
        """
root_fields:
  workflow_step: scalar_step
  output_scope: document_root
  fields:
    line_items:
      workflow_output_key: line_items
      prompt:
        instructions: Return the line item summary.
        type: str

line_items:
  workflow_step: repeated_step
  fields:
    description:
      workflow_output_key: description
      prompt:
        instructions: Return each description.
        type: str
"""
    )

    with pytest.raises(ValueError, match="conflicting final paths"):
        prepare_extraction_yaml(raw)


def test_literal_meter_number_and_empty_match_attrs_do_not_create_relationship() -> None:
    prepared = prepare_extraction_yaml(
        _workflow_yaml(
            """
parent_rows:
  workflow_step: repeated_step
  fields:
    meter_number:
      workflow_output_key: meter_number
      prompt:
        instructions: Return the generic parent identifier.
        type: str

child_rows:
  workflow_step: repeated_step
  match_attrs: []
  passthrough:
    from: parent_rows
  fields:
    meter_number:
      workflow_output_key: child_meter_number
      prompt:
        instructions: Return the generic child identifier.
        type: str
"""
        )
    )

    workflow = prepared.persisted_workflow_extract["workflow"]
    assert workflow.get("output_relationships") is None
    assert [route["final_path"] for route in workflow["output_routes"]] == [
        "/parent_rows/*/meter_number",
        "/child_rows/*/meter_number",
    ]
