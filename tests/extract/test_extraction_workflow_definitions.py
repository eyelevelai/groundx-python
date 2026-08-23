import copy
import inspect
import typing
from pathlib import Path

import pytest
import yaml

from groundx import AsyncGroundX, GroundX
from groundx.core.request_options import RequestOptions
from groundx.extract import prepare_extraction_yaml
from groundx.types import (
    WorkflowDetail,
    WorkflowResponse,
    WorkflowStep,
    WorkflowStepConfig,
    WorkflowSteps,
)

CUSTOM_WORKFLOW_YAML = """
extraction_policy_version: v1

workflow:
  template:
    "{{LANGUAGE}}": English
    "{{LANGUAGE_UNKNOWN}}": ""
  custom_steps:
    - name: line_item_labels
      level: chunk
      kind: keys
      required_template_keys:
        - "{{LANGUAGE}}"
      config:
        all:
          includes:
            text: true

line_items:
  workflow_step: line_item_labels
  fields:
    description:
      workflow_output_key: label
      prompt:
        identifiers:
          - Description
        instructions: Return the printed line-item description.
        type: str
"""

ADP_WORKFLOW_SOURCE: dict[str, typing.Any] = {
    "extraction_policy_version": "v1",
    "_groundx_internal_capture": {"enabled": True},
    "workflow": {
        "section_strategy": "page",
        "custom_steps": [
            {
                "name": "adp_f1",
                "level": "section",
                "kind": "keys",
                "config": {"all": {"includes": {"text": True}}},
            }
        ],
    },
    "plan_information": {
        "role": "statement",
        "fields": {
            "plan_name": {
                "prompt": {
                    "instructions": "Return the plan name.",
                    "type": "str",
                }
            }
        },
    },
    "_pseudo_groups": {
        "adp_f1_employer_and_plan_information": {
            "role": "statement",
            "workflow_step": "adp_f1",
            "fields": {"plan_name": {"path": "/plan_information/plan_name"}},
        }
    },
}

V1_CONTRACT_YAML = Path(__file__).parent / "prompt" / "fixtures" / "extraction_yaml_contract_v1.yaml"


EXECUTION_ONLY_EXTRACT = {
    "line_items": {
        "fields": {
            "description": {
                "prompt": {
                    "identifiers": ["Description"],
                    "instructions": "Return the printed line-item description.",
                    "type": "str",
                }
            }
        }
    },
    "workflow": {
        "metadata_version": 1,
        "template": {
            "{{LANGUAGE}}": "English",
            "{{LANGUAGE_UNKNOWN}}": "",
        },
        "custom_steps": [
            {
                "name": "line_item_labels",
                "level": "chunk",
                "kind": "keys",
                "required_template_keys": ["{{LANGUAGE}}"],
            }
        ],
        "output_routes": [
            {
                "workflow_group": "line_items",
                "workflow_field": "description",
                "final_path": "/line_items/description",
                "step_name": "line_item_labels",
                "level": "chunk",
                "output_map": "customChunkOutputs",
                "output_key": "label",
                "readback_path": ("/chunks/*/customChunkOutputs/line_item_labels/label"),
            }
        ],
        "leaf_fields": [
            {
                "final_path": "/line_items/description",
                "workflow_group": "line_items",
                "workflow_field": "description",
                "step_name": "line_item_labels",
                "level": "chunk",
                "output_key": "label",
                "field_type": "str",
                "is_repeated": False,
                "repetition_scope": "none",
            }
        ],
    },
}


class RecordingWorkflows:
    def __init__(self, response: typing.Optional[WorkflowResponse] = None) -> None:
        self.response = response
        self.calls: typing.List[typing.Tuple[typing.Any, ...]] = []

    def create(self, **kwargs: typing.Any) -> str:
        self.calls.append(("create", kwargs))
        return "created"

    def update(self, id: str, **kwargs: typing.Any) -> str:
        self.calls.append(("update", id, kwargs))
        return "updated"

    def get(
        self,
        id: str,
        *,
        request_options: typing.Optional[typing.Mapping[str, typing.Any]] = None,
    ) -> WorkflowResponse:
        self.calls.append(("get", id, request_options))
        if self.response is None:
            raise AssertionError("missing workflow response")
        return self.response


class AsyncRecordingWorkflows:
    def __init__(self, response: typing.Optional[WorkflowResponse] = None) -> None:
        self.response = response
        self.calls: typing.List[typing.Tuple[typing.Any, ...]] = []

    async def create(self, **kwargs: typing.Any) -> str:
        self.calls.append(("create", kwargs))
        return "created"

    async def update(self, id: str, **kwargs: typing.Any) -> str:
        self.calls.append(("update", id, kwargs))
        return "updated"

    async def get(
        self,
        id: str,
        *,
        request_options: typing.Optional[typing.Mapping[str, typing.Any]] = None,
    ) -> WorkflowResponse:
        self.calls.append(("get", id, request_options))
        if self.response is None:
            raise AssertionError("missing workflow response")
        return self.response


def _client(workflows: RecordingWorkflows) -> GroundX:
    client = GroundX.__new__(GroundX)
    typing.cast(typing.Any, client)._workflows = workflows
    return client


def _async_client(workflows: AsyncRecordingWorkflows) -> AsyncGroundX:
    client = AsyncGroundX.__new__(AsyncGroundX)
    typing.cast(typing.Any, client)._workflows = workflows
    return client


def _step_value(value: typing.Any, field: str) -> typing.Any:
    if isinstance(value, dict):
        return typing.cast(typing.Dict[str, typing.Any], value)[field]
    return getattr(value, field)


def _find_mapping_keys(
    value: typing.Any,
    keys: typing.Set[str],
    path: str = "$",
) -> typing.List[str]:
    matches: typing.List[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in keys:
                matches.append(child_path)
            matches.extend(_find_mapping_keys(child, keys, child_path))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            matches.extend(_find_mapping_keys(child, keys, f"{path}[{idx}]"))
    return matches


def test_load_definition_from_yaml_path_preserves_template_and_prepared(
    tmp_path: Path,
) -> None:
    path = tmp_path / "statement.yaml"
    path.write_text(CUSTOM_WORKFLOW_YAML)

    definition = _client(RecordingWorkflows()).load_extraction_definition_from_yaml(path=path)

    assert definition.prepared is not None
    assert definition.extract == definition.prepared.persisted_workflow_extract
    assert definition.template == {
        "{{LANGUAGE}}": "English",
        "{{LANGUAGE_UNKNOWN}}": "",
    }
    assert definition.custom_steps[0]["name"] == "line_item_labels"
    assert definition.output_routes[0]["output_key"] == "label"
    assert definition.leaf_fields[0]["field_type"] == "str"


def test_persisted_custom_workflow_authored_copy_is_runtime_safe() -> None:
    prepared = prepare_extraction_yaml(CUSTOM_WORKFLOW_YAML)
    persisted = prepared.persisted_workflow_extract
    authored_copy = persisted["_groundx_persisted_extract"]

    assert authored_copy["workflow"]["metadata_version"] == 1
    assert (
        _find_mapping_keys(
            authored_copy,
            {"workflow_step", "workflow_output_key"},
        )
        == []
    )

    reloaded = prepare_extraction_yaml(persisted)
    standalone = prepare_extraction_yaml(authored_copy)

    assert reloaded.persisted_workflow_extract["workflow"]["output_routes"] == (persisted["workflow"]["output_routes"])
    assert standalone.persisted_workflow_extract["workflow"]["leaf_fields"] == (persisted["workflow"]["leaf_fields"])


def test_load_extraction_definition_uses_yaml_path(tmp_path: Path) -> None:
    path = tmp_path / "statement.yaml"
    path.write_text(CUSTOM_WORKFLOW_YAML)

    definition = _client(RecordingWorkflows()).load_extraction_definition(path=path)

    assert definition.prepared is not None
    assert definition.template == {
        "{{LANGUAGE}}": "English",
        "{{LANGUAGE_UNKNOWN}}": "",
    }
    assert definition.custom_steps[0]["name"] == "line_item_labels"


def test_load_extraction_definition_uses_workflow_id() -> None:
    response = WorkflowResponse(
        workflow=WorkflowDetail(
            workflow_id="workflow-1",
            extract=EXECUTION_ONLY_EXTRACT,
            template={"{{LANGUAGE}}": "English", "{{LANGUAGE_UNKNOWN}}": ""},
        )
    )
    workflows = RecordingWorkflows(response)
    request_options: RequestOptions = {"timeout_in_seconds": 1}

    definition = _client(workflows).load_extraction_definition(
        workflow_id="workflow-1",
        request_options=request_options,
    )

    assert workflows.calls == [("get", "workflow-1", request_options)]
    assert definition.extract == EXECUTION_ONLY_EXTRACT
    assert definition.template["{{LANGUAGE_UNKNOWN}}"] == ""


def test_workflow_readback_does_not_recompile_historical_authored_snapshot() -> None:
    extract = copy.deepcopy(prepare_extraction_yaml(CUSTOM_WORKFLOW_YAML).persisted_workflow_extract)
    extract["_groundx_persisted_extract"]["line_items"]["final_value_aliases"] = {"description": "label"}
    response = WorkflowResponse(
        workflow=WorkflowDetail(
            workflow_id="historical-workflow",
            extract=typing.cast(typing.Any, extract),
        )
    )

    definition = _client(RecordingWorkflows(response)).load_extraction_definition(workflow_id="historical-workflow")

    assert definition.extract == extract
    assert definition.prepared is None


def test_workflow_extract_mapping_does_not_revalidate_authored_agent_chain() -> None:
    extract = copy.deepcopy(prepare_extraction_yaml(V1_CONTRACT_YAML.read_text()).persisted_workflow_extract)
    partial_chain = [
        {
            "parallel": [
                {
                    "group": "statement_identity",
                    "chain": ["reconcile_statement", "qa_statement"],
                }
            ]
        },
        "save_statement",
    ]
    extract["workflow"]["agent_chain"] = copy.deepcopy(partial_chain)
    extract["_groundx_persisted_extract"]["workflow"]["agent_chain"] = copy.deepcopy(partial_chain)

    definition = _client(RecordingWorkflows()).load_extraction_definition_from_yaml(
        mapping=extract,
        mapping_kind="workflow_extract",
    )

    assert definition.extract == extract
    assert definition.prepared is None


def test_load_extraction_definition_uses_workflow_id_before_yaml_sources(tmp_path: Path) -> None:
    path = tmp_path / "statement.yaml"
    path.write_text("not: [valid")
    response = WorkflowResponse(
        workflow=WorkflowDetail(
            workflow_id="workflow-1",
            extract=EXECUTION_ONLY_EXTRACT,
            template={"{{LANGUAGE}}": "English", "{{LANGUAGE_UNKNOWN}}": ""},
        )
    )
    workflows = RecordingWorkflows(response)
    request_options: RequestOptions = {"timeout_in_seconds": 1}

    definition = _client(workflows).load_extraction_definition(
        workflow_id="workflow-1",
        path=path,
        request_options=request_options,
    )

    assert workflows.calls == [("get", "workflow-1", request_options)]
    assert definition.extract == EXECUTION_ONLY_EXTRACT


def test_load_extraction_definition_rejects_mapping_kind_with_workflow_id() -> None:
    response = WorkflowResponse(
        workflow=WorkflowDetail(
            workflow_id="workflow-1",
            extract=EXECUTION_ONLY_EXTRACT,
        )
    )

    with pytest.raises(ValueError, match="mapping_kind"):
        _client(RecordingWorkflows(response)).load_extraction_definition(
            workflow_id="workflow-1",
            mapping_kind="workflow_extract",
        )


def test_load_extraction_definition_rejects_missing_or_ambiguous_yaml_sources(tmp_path: Path) -> None:
    path = tmp_path / "statement.yaml"
    path.write_text(CUSTOM_WORKFLOW_YAML)

    with pytest.raises(ValueError, match="exactly one"):
        _client(RecordingWorkflows()).load_extraction_definition()
    with pytest.raises(ValueError, match="exactly one"):
        _client(RecordingWorkflows()).load_extraction_definition(
            path=path,
            yaml_text=CUSTOM_WORKFLOW_YAML,
        )
    with pytest.raises(ValueError, match="request_options"):
        _client(RecordingWorkflows()).load_extraction_definition(
            path=path,
            request_options={"timeout_in_seconds": 1},
        )


def test_load_definition_from_mapping_defaults_to_authored_yaml() -> None:
    mapping = typing.cast(
        typing.Dict[str, typing.Any],
        yaml.safe_load(CUSTOM_WORKFLOW_YAML),
    )

    definition = _client(RecordingWorkflows()).load_extraction_definition_from_yaml(mapping=mapping)

    assert definition.prepared is not None
    assert definition.template["{{LANGUAGE}}"] == "English"
    assert definition.template["{{LANGUAGE_UNKNOWN}}"] == ""


def test_workflow_extract_mapping_requires_explicit_kind() -> None:
    persisted = prepare_extraction_yaml(CUSTOM_WORKFLOW_YAML).persisted_workflow_extract

    client = _client(RecordingWorkflows())
    with pytest.raises(ValueError, match="mapping_kind"):
        client.load_extraction_definition_from_yaml(mapping=persisted)

    definition = client.load_extraction_definition_from_yaml(
        mapping=persisted,
        mapping_kind="workflow_extract",
    )

    assert definition.extract == persisted
    assert definition.prepared is None
    assert definition.template == {
        "{{LANGUAGE}}": "English",
        "{{LANGUAGE_UNKNOWN}}": "",
    }


def test_workflow_extract_without_authored_metadata_returns_no_prepared() -> None:
    definition = _client(RecordingWorkflows()).load_extraction_definition_from_yaml(
        mapping=EXECUTION_ONLY_EXTRACT,
        mapping_kind="workflow_extract",
    )

    assert definition.prepared is None
    assert definition.extract == EXECUTION_ONLY_EXTRACT
    assert definition.template["{{LANGUAGE_UNKNOWN}}"] == ""
    assert definition.custom_steps[0]["name"] == "line_item_labels"


def test_workflow_extract_rejects_custom_metadata_without_version() -> None:
    mapping = typing.cast(
        typing.Dict[str, typing.Any],
        yaml.safe_load(CUSTOM_WORKFLOW_YAML),
    )
    extract = prepare_extraction_yaml(mapping).persisted_workflow_extract
    del extract["workflow"]["metadata_version"]

    with pytest.raises(ValueError, match="metadata_version"):
        _client(RecordingWorkflows()).load_extraction_definition_from_yaml(
            mapping=extract,
            mapping_kind="workflow_extract",
        )


def test_workflow_extract_rejects_authoring_markers_without_metadata() -> None:
    extract = {
        "line_items": {
            "workflow_step": "line_item_labels",
            "fields": {
                "description": {
                    "workflow_output_key": "label",
                    "prompt": {
                        "instructions": "Return the printed line-item description.",
                        "type": "str",
                    },
                }
            },
        }
    }

    with pytest.raises(ValueError, match="authoring-only"):
        _client(RecordingWorkflows()).load_extraction_definition_from_yaml(
            mapping=extract,
            mapping_kind="workflow_extract",
        )


def test_workflow_extract_rejects_route_to_missing_group() -> None:
    extract = typing.cast(
        typing.Dict[str, typing.Any],
        copy.deepcopy(EXECUTION_ONLY_EXTRACT),
    )
    workflow = typing.cast(typing.Dict[str, typing.Any], extract["workflow"])
    workflow["output_routes"][0]["workflow_group"] = "missing_items"
    workflow["leaf_fields"][0]["workflow_group"] = "missing_items"

    with pytest.raises(ValueError, match="missing_items"):
        _client(RecordingWorkflows()).load_extraction_definition_from_yaml(
            mapping=extract,
            mapping_kind="workflow_extract",
        )


def test_template_values_must_be_strings() -> None:
    mapping = typing.cast(
        typing.Dict[str, typing.Any],
        yaml.safe_load(CUSTOM_WORKFLOW_YAML),
    )
    mapping["workflow"]["template"]["{{LANGUAGE}}"] = ["English"]

    with pytest.raises(ValueError, match=r"\{\{LANGUAGE\}\}"):
        _client(RecordingWorkflows()).load_extraction_definition_from_yaml(mapping=mapping)


def test_load_definition_from_workflow_preserves_top_level_workflow_fields() -> None:
    response = WorkflowResponse(
        workflow=WorkflowDetail(
            workflow_id="workflow-1",
            name="workflow name",
            extract=EXECUTION_ONLY_EXTRACT,
            template={"{{LANGUAGE}}": "French", "{{LANGUAGE_UNKNOWN}}": ""},
            custom_steps=typing.cast(
                typing.Any,
                [
                    {
                        "name": "top_level_labels",
                        "level": "chunk",
                        "kind": "keys",
                        "requiredTemplateKeys": ["{{LANGUAGE}}"],
                    }
                ],
            ),
            output_routes=typing.cast(
                typing.Any,
                [
                    {
                        "workflowGroup": "line_items",
                        "workflowField": "description",
                        "finalPath": "/line_items/description",
                        "stepName": "top_level_labels",
                        "level": "chunk",
                        "outputMap": "customChunkOutputs",
                        "outputKey": "label",
                        "readbackPath": ("/chunks/*/customChunkOutputs/top_level_labels/label"),
                    }
                ],
            ),
            leaf_fields=typing.cast(
                typing.Any,
                [
                    {
                        "finalPath": "/line_items/description",
                        "workflowGroup": "line_items",
                        "workflowField": "description",
                        "stepName": "top_level_labels",
                        "level": "chunk",
                        "outputKey": "label",
                        "fieldType": "str",
                        "isRepeated": False,
                        "repetitionScope": "none",
                    }
                ],
            ),
            chunk_strategy="size",
            section_strategy="page",
            steps=WorkflowSteps(chunk_keys=WorkflowStep(all_=WorkflowStepConfig(includes={"text": True}))),
        )
    )
    workflows = RecordingWorkflows(response)
    request_options: RequestOptions = {"timeout_in_seconds": 1}

    definition = _client(workflows).load_extraction_definition_from_workflow(
        "workflow-1",
        request_options=request_options,
    )

    assert workflows.calls == [("get", "workflow-1", request_options)]
    assert definition.prepared is None
    assert definition.template == {
        "{{LANGUAGE}}": "French",
        "{{LANGUAGE_UNKNOWN}}": "",
    }
    assert _step_value(definition.custom_steps[0], "name") == "top_level_labels"
    assert _step_value(definition.custom_steps[0], "required_template_keys") == ["{{LANGUAGE}}"]
    assert _step_value(definition.output_routes[0], "step_name") == "top_level_labels"
    assert _step_value(definition.output_routes[0], "output_key") == "label"
    assert _step_value(definition.leaf_fields[0], "step_name") == "top_level_labels"
    assert _step_value(definition.leaf_fields[0], "field_type") == "str"
    assert definition.chunk_strategy == "size"
    assert definition.section_strategy == "page"
    assert _step_value(definition.steps, "chunk_keys") is not None


def test_load_definition_from_workflow_requires_extract() -> None:
    response = WorkflowResponse(workflow=WorkflowDetail(workflow_id="workflow-1", name="workflow name"))

    with pytest.raises(ValueError, match="workflow-1"):
        _client(RecordingWorkflows(response)).load_extraction_definition_from_workflow("workflow-1")


def test_load_adp_workflow_readback_preserves_section_strategy() -> None:
    extract = copy.deepcopy(prepare_extraction_yaml(ADP_WORKFLOW_SOURCE).persisted_workflow_extract)
    response = WorkflowResponse(
        workflow=WorkflowDetail(
            workflow_id="adp-v1",
            name="ADP v1",
            extract=typing.cast(typing.Any, extract),
        )
    )

    client = _client(RecordingWorkflows(response))
    definition = client.load_extraction_definition_from_workflow("adp-v1")
    mapping_definition = client.load_extraction_definition_from_yaml(
        mapping=extract,
        mapping_kind="workflow_extract",
    )

    assert definition.prepared is None
    assert mapping_definition.prepared is None
    assert definition.section_strategy == "page"
    assert mapping_definition.section_strategy == "page"


def test_prepare_adp_persisted_source_preserves_runtime_metadata() -> None:
    workflow_extract = prepare_extraction_yaml(ADP_WORKFLOW_SOURCE).persisted_workflow_extract
    persisted_source = workflow_extract["_groundx_persisted_extract"]

    prepared = prepare_extraction_yaml(persisted_source)
    client = _client(RecordingWorkflows())
    prepared_definition = client.load_extraction_definition_from_yaml(prepared=prepared)
    persisted_definition = client.load_extraction_definition_from_yaml(
        mapping=prepared.persisted_workflow_extract,
        mapping_kind="workflow_extract",
    )

    assert prepared.persisted_workflow_extract["workflow"]["section_strategy"] == "page"
    assert prepared_definition.section_strategy == "page"
    assert persisted_definition.section_strategy == "page"
    assert prepared.top_level_metadata["_groundx_internal_capture"]["enabled"] is True
    assert prepared.workflow_group_metadata["adp_f1_employer_and_plan_information"]["role"] == "statement"


def test_create_and_update_forward_raw_yaml_and_request_options() -> None:
    workflows = RecordingWorkflows()
    client = _client(workflows)
    request_options: RequestOptions = {"timeout_in_seconds": 1}

    assert (
        client.create_extraction_workflow(
            yaml_text=CUSTOM_WORKFLOW_YAML,
            name="statement extraction",
            request_options=request_options,
        )
        == "created"
    )
    assert (
        client.update_extraction_workflow(
            "workflow-1",
            yaml_text=CUSTOM_WORKFLOW_YAML,
            name="statement extraction",
            request_options=request_options,
        )
        == "updated"
    )

    create_kwargs = workflows.calls[0][1]
    update_kwargs = workflows.calls[1][2]

    assert create_kwargs["name"] == "statement extraction"
    assert create_kwargs["request_options"] is request_options
    assert update_kwargs["name"] == "statement extraction"
    assert update_kwargs["request_options"] is request_options
    assert create_kwargs["yaml"] == CUSTOM_WORKFLOW_YAML
    assert update_kwargs["yaml"] == CUSTOM_WORKFLOW_YAML
    assert set(create_kwargs) == {"name", "yaml", "request_options"}
    assert set(update_kwargs) == {"name", "yaml", "request_options"}


def test_update_helper_exposes_no_client_side_downgrade_option() -> None:
    signature = inspect.signature(GroundX.update_extraction_workflow)

    assert "allow_legacy_downgrade" not in signature.parameters
    assert "existing_workflow" not in signature.parameters


def test_create_requires_name_but_update_can_omit_name() -> None:
    workflows = RecordingWorkflows()
    client = _client(workflows)

    with pytest.raises(ValueError, match="name"):
        client.create_extraction_workflow(yaml_text=CUSTOM_WORKFLOW_YAML)

    assert (
        client.update_extraction_workflow(
            "workflow-1",
            yaml_text=CUSTOM_WORKFLOW_YAML,
        )
        == "updated"
    )
    assert "name" not in workflows.calls[0][2]


@pytest.mark.asyncio
async def test_async_workflow_readback_preserves_server_metadata() -> None:
    response = WorkflowResponse(
        workflow=WorkflowDetail(
            workflow_id="workflow-1",
            extract=EXECUTION_ONLY_EXTRACT,
            template={"{{LANGUAGE}}": "English", "{{LANGUAGE_UNKNOWN}}": ""},
        )
    )
    workflows = AsyncRecordingWorkflows(response)
    client = _async_client(workflows)
    request_options: RequestOptions = {"timeout_in_seconds": 1}

    definition = await client.load_extraction_definition_from_workflow(
        "workflow-1",
        request_options=request_options,
    )

    assert workflows.calls == [("get", "workflow-1", request_options)]
    assert definition.extract == EXECUTION_ONLY_EXTRACT
    assert definition.template == {
        "{{LANGUAGE}}": "English",
        "{{LANGUAGE_UNKNOWN}}": "",
    }
    assert definition.prepared is None
