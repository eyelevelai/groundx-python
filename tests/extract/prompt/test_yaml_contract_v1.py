import json
from pathlib import Path
import typing

import pytest

from groundx import GroundX
from groundx.extract import prepare_extraction_yaml


FIXTURE_DIR = Path(__file__).parent / "fixtures"
CONTRACT_YAML = FIXTURE_DIR / "extraction_yaml_contract_v1.yaml"
EXPECTED_JSON = FIXTURE_DIR / "extraction_yaml_contract_v1.expected.json"


class RecordingWorkflows:
    def __init__(self, response: typing.Any = None) -> None:
        self.response = response
        self.calls: typing.List[typing.Tuple[typing.Any, ...]] = []

    def create(self, **kwargs: typing.Any) -> str:
        self.calls.append(("create", kwargs))
        return "created"

    def update(self, id: str, **kwargs: typing.Any) -> str:
        self.calls.append(("update", id, kwargs))
        return "updated"


def _client(workflows: RecordingWorkflows) -> GroundX:
    client = GroundX.__new__(GroundX)
    typing.cast(typing.Any, client)._workflows = workflows
    return client


def test_contract_fixture_compiles_to_expected_payload() -> None:
    prepared = prepare_extraction_yaml(CONTRACT_YAML.read_text())
    observed = {
        "groups": prepared.groups,
        "workflow_groups": prepared.workflow_groups,
        "pseudo_groups": prepared.pseudo_groups,
        "workflow_field_paths": prepared.workflow_field_paths,
        "top_level_metadata": prepared.top_level_metadata,
        "final_group_metadata": prepared.final_group_metadata,
        "workflow_group_metadata": prepared.workflow_group_metadata,
        "persisted_workflow_extract": prepared.persisted_workflow_extract,
    }

    assert observed == json.loads(EXPECTED_JSON.read_text())


def test_pseudo_groups_create_custom_workflow_routes_and_preserve_agent_chain() -> None:
    prepared = prepare_extraction_yaml(CONTRACT_YAML.read_text())
    workflow = prepared.persisted_workflow_extract["workflow"]
    authored = prepared.persisted_workflow_extract["_groundx_persisted_extract"]

    assert workflow["agent_chain"] == authored["workflow"]["agent_chain"]
    assert [route["workflow_group"] for route in workflow["output_routes"]] == [
        "statement_identity",
        "statement_totals",
    ]
    assert [route["output_key"] for route in workflow["output_routes"]] == [
        "account_number",
        "total_amount_due",
    ]
    assert [route["final_path"] for route in workflow["output_routes"]] == [
        "/statement/account_number",
        "/statement/total_amount_due",
    ]
    assert "workflow_step" not in authored["_pseudo_groups"]["statement_identity"]
    assert "workflow_output_key" not in json.dumps(authored)


def test_create_update_persist_agent_chain_only_inside_extract() -> None:
    workflows = RecordingWorkflows()
    client = _client(workflows)

    client.create_extraction_workflow(path=CONTRACT_YAML, name="statement extraction")
    client.update_extraction_workflow(
        "workflow-1",
        path=CONTRACT_YAML,
        name="statement extraction",
    )

    create_kwargs = workflows.calls[0][1]
    update_kwargs = workflows.calls[1][2]
    for kwargs in (create_kwargs, update_kwargs):
        assert "agent_chain" not in kwargs
        assert kwargs["extract"]["workflow"]["agent_chain"] == (
            kwargs["extract"]["_groundx_persisted_extract"]["workflow"]["agent_chain"]
        )


def test_agent_chain_rejects_map_shape() -> None:
    raw = """
extraction_policy_version: v1

workflow:
  custom_steps:
    - name: statement_fields
      level: chunk
      kind: instruct
  agent_chain:
    parallel:
      - group: statement
        chain: [reconcile_statement, qa_statement]
    then:
      - save_statement

statement:
  workflow_step: statement_fields
  fields:
    account_number:
      workflow_output_key: account_number
      prompt:
        instructions: Return the account number.
        type: str
"""

    with pytest.raises(ValueError, match="workflow.agent_chain must be a list"):
        prepare_extraction_yaml(raw)


def test_agent_chain_rejects_chain_without_initial_parallel_stage() -> None:
    raw = """
extraction_policy_version: v1

workflow:
  custom_steps:
    - name: statement_fields
      level: chunk
      kind: instruct
  agent_chain:
    - save_statement

statement:
  workflow_step: statement_fields
  fields:
    account_number:
      workflow_output_key: account_number
      prompt:
        instructions: Return the account number.
        type: str
"""

    with pytest.raises(
        ValueError,
        match="workflow.agent_chain must start with a parallel stage",
    ):
        prepare_extraction_yaml(raw)


def test_agent_chain_rejects_unknown_group_and_task() -> None:
    unknown_group = """
extraction_policy_version: v1

workflow:
  custom_steps:
    - name: statement_fields
      level: chunk
      kind: instruct
  agent_chain:
    - parallel:
        - group: missing
          chain: [reconcile_statement, qa_statement]
    - save_statement

statement:
  workflow_step: statement_fields
  fields:
    account_number:
      workflow_output_key: account_number
      prompt:
        instructions: Return the account number.
        type: str
"""

    with pytest.raises(ValueError, match="missing.*is not a workflow group"):
        prepare_extraction_yaml(unknown_group)

    unknown_task = unknown_group.replace(
        "reconcile_statement", "unknown_task"
    ).replace("missing", "statement")
    with pytest.raises(ValueError, match="unsupported task"):
        prepare_extraction_yaml(unknown_task)


def test_agent_chain_rejects_branch_save_plus_top_level_save() -> None:
    raw = """
extraction_policy_version: v1

workflow:
  custom_steps:
    - name: statement_fields
      level: chunk
      kind: instruct
  agent_chain:
    - parallel:
        - group: statement
          chain: [reconcile_statement, qa_statement, save_statement]
    - save_statement

statement:
  workflow_step: statement_fields
  fields:
    account_number:
      workflow_output_key: account_number
      prompt:
        instructions: Return the account number.
        type: str
"""

    with pytest.raises(
        ValueError,
        match="parallel branch save tasks cannot be combined",
    ):
        prepare_extraction_yaml(raw)


def test_agent_chain_rejects_invalid_top_level_serial_task_pairs() -> None:
    base = """
extraction_policy_version: v1

workflow:
  custom_steps:
    - name: statement_fields
      level: chunk
      kind: instruct
  agent_chain:
{agent_chain}

statement:
  workflow_step: statement_fields
  fields:
    account_number:
      workflow_output_key: account_number
      prompt:
        instructions: Return the account number.
        type: str
"""
    cases = [
        """
    - parallel:
        - group: statement
          chain: [reconcile_statement, qa_statement, save_statement]
    - reconcile_charges
""",
        """
    - parallel:
        - group: statement
          chain: [reconcile_statement, qa_statement, save_statement]
    - reconcile_charges
    - save_statement
""",
        """
    - parallel:
        - group: statement
          chain: [reconcile_statement, qa_statement]
    - save_statement
    - reconcile_charges
""",
    ]

    for agent_chain in cases:
        with pytest.raises(ValueError, match="top-level agent task"):
            prepare_extraction_yaml(base.format(agent_chain=agent_chain))


def test_slot_and_domain_are_rejected_even_with_metadata_escape_hatches() -> None:
    raw = """
domain: invoice
statement:
  slot: chunk-instruct
  fields:
    account_number:
      prompt:
        instructions: Return the account number.
        type: str
"""

    with pytest.raises(ValueError, match="domain"):
        prepare_extraction_yaml(
            raw,
            top_level_metadata_keys={"domain"},
            workflow_group_metadata_keys={"slot"},
        )


def test_pure_legacy_yaml_rejects_extraction_policy_version() -> None:
    raw = """
extraction_policy_version: v1
statement:
  fields:
    account_number:
      prompt:
        instructions: Return the account number.
        type: str
"""

    with pytest.raises(ValueError, match="extraction_policy_version"):
        prepare_extraction_yaml(raw)


def test_new_yaml_requires_extraction_policy_version() -> None:
    raw = """
workflow:
  custom_steps:
    - name: statement_fields
      level: chunk
      kind: keys
statement:
  workflow_step: statement_fields
  fields:
    account_number:
      workflow_output_key: account_number
      prompt:
        instructions: Return the account number.
        type: str
"""

    with pytest.raises(ValueError, match="extraction_policy_version: v1"):
        prepare_extraction_yaml(raw)


def test_field_level_workflow_step_is_rejected() -> None:
    raw = """
extraction_policy_version: v1
workflow:
  custom_steps:
    - name: statement_fields
      level: chunk
      kind: keys
statement:
  fields:
    account_number:
      workflow_step: statement_fields
      workflow_output_key: account_number
      prompt:
        instructions: Return the account number.
        type: str
"""

    with pytest.raises(ValueError, match="field-level workflow_step"):
        prepare_extraction_yaml(raw)


def test_pseudo_field_keys_must_be_safe_output_keys() -> None:
    raw = """
extraction_policy_version: v1
statement:
  fields:
    account_number:
      prompt:
        instructions: Return the account number.
        type: str
_pseudo_groups:
  statement_identity:
    fields:
      Account Number:
        path: /statement/account_number
"""

    with pytest.raises(ValueError, match="invalid output key"):
        prepare_extraction_yaml(raw)


def test_pseudo_routed_final_fields_cannot_declare_workflow_output_key() -> None:
    raw = """
extraction_policy_version: v1
workflow:
  custom_steps:
    - name: statement_fields
      level: chunk
      kind: keys
statement:
  fields:
    account_number:
      workflow_output_key: account_number
      prompt:
        instructions: Return the account number.
        type: str
_pseudo_groups:
  statement_identity:
    workflow_step: statement_fields
    fields:
      account_number:
        path: /statement/account_number
"""

    with pytest.raises(ValueError, match="pseudo-routed"):
        prepare_extraction_yaml(raw)
