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


def _model_to_alias_dict(value: typing.Any) -> typing.Dict[str, typing.Any]:
    if isinstance(value, dict):
        return typing.cast(typing.Dict[str, typing.Any], value)
    if hasattr(value, "dict"):
        return typing.cast(typing.Dict[str, typing.Any], value.dict())
    return typing.cast(
        typing.Dict[str, typing.Any],
        value.model_dump(by_alias=True, exclude_none=False),
    )


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
    assert _find_mapping_keys(
        authored_copy,
        {"workflow_step", "workflow_output_key"},
    ) == []

    reloaded = prepare_extraction_yaml(persisted)
    standalone = prepare_extraction_yaml(authored_copy)

    assert reloaded.persisted_workflow_extract["workflow"]["output_routes"] == (
        persisted["workflow"]["output_routes"]
    )
    assert standalone.persisted_workflow_extract["workflow"]["leaf_fields"] == (
        persisted["workflow"]["leaf_fields"]
    )


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
    assert definition.prepared is not None
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


def test_create_and_update_use_definition_before_yaml_sources() -> None:
    client = _client(RecordingWorkflows())
    definition = client.load_extraction_definition_from_yaml(yaml_text=CUSTOM_WORKFLOW_YAML)

    assert (
        client.create_extraction_workflow(
            definition=definition,
            yaml_text="not: [valid",
            name="statement extraction",
        )
        == "created"
    )
    assert (
        client.update_extraction_workflow(
            "workflow-1",
            definition=definition,
            yaml_text="not: [valid",
            name="statement extraction",
        )
        == "updated"
    )

    assert client.workflows.calls[0][1]["extract"] == definition.extract
    assert client.workflows.calls[1][2]["extract"] == definition.extract


def test_create_and_update_reject_mapping_kind_with_definition() -> None:
    client = _client(RecordingWorkflows())
    definition = client.load_extraction_definition_from_yaml(yaml_text=CUSTOM_WORKFLOW_YAML)

    with pytest.raises(ValueError, match="mapping_kind"):
        client.create_extraction_workflow(
            definition=definition,
            mapping_kind="workflow_extract",
            name="statement extraction",
        )

    with pytest.raises(ValueError, match="mapping_kind"):
        client.update_extraction_workflow(
            "workflow-1",
            definition=definition,
            mapping_kind="workflow_extract",
            name="statement extraction",
        )


def test_create_and_update_reject_missing_or_ambiguous_yaml_sources() -> None:
    client = _client(RecordingWorkflows())

    with pytest.raises(ValueError, match="exactly one"):
        client.create_extraction_workflow(name="statement extraction")
    with pytest.raises(ValueError, match="path.*yaml_text|yaml_text.*path"):
        client.create_extraction_workflow(
            path="statement.yaml",
            yaml_text=CUSTOM_WORKFLOW_YAML,
            name="statement extraction",
        )
    with pytest.raises(ValueError, match="mapping_kind"):
        client.create_extraction_workflow(
            yaml_text=CUSTOM_WORKFLOW_YAML,
            mapping_kind="workflow_extract",
            name="statement extraction",
        )


def test_create_and_update_forward_workflow_settings_and_request_options() -> None:
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
    assert create_kwargs["template"] == {
        "{{LANGUAGE}}": "English",
        "{{LANGUAGE_UNKNOWN}}": "",
    }
    assert create_kwargs["extract"]["workflow"]["template"] == {
        "{{LANGUAGE}}": "English",
        "{{LANGUAGE_UNKNOWN}}": "",
    }
    assert create_kwargs["custom_steps"][0]["name"] == "line_item_labels"
    assert create_kwargs["output_routes"][0]["output_key"] == "label"
    assert create_kwargs["leaf_fields"][0]["field_type"] == "str"
    assert update_kwargs["extract"] == create_kwargs["extract"]


def test_create_and_update_accept_yaml_path_shortcut(tmp_path: Path) -> None:
    path = tmp_path / "statement.yaml"
    path.write_text(CUSTOM_WORKFLOW_YAML)
    workflows = RecordingWorkflows()
    client = _client(workflows)

    assert (
        client.create_extraction_workflow(
            path=path,
            name="statement extraction",
        )
        == "created"
    )
    assert (
        client.update_extraction_workflow(
            "workflow-1",
            path=path,
            name="statement extraction",
        )
        == "updated"
    )

    create_kwargs = workflows.calls[0][1]
    update_kwargs = workflows.calls[1][2]
    assert create_kwargs["extract"] == update_kwargs["extract"]
    assert create_kwargs["template"] == {
        "{{LANGUAGE}}": "English",
        "{{LANGUAGE_UNKNOWN}}": "",
    }


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


def test_custom_steps_disable_exact_fixed_default_overlay() -> None:
    workflows = RecordingWorkflows()
    client = _client(workflows)

    client.create_extraction_workflow(
        yaml_text=CUSTOM_WORKFLOW_YAML,
        name="statement extraction",
    )

    steps = workflows.calls[0][1]["steps"]
    assert _model_to_alias_dict(steps) == {
        "chunk-instruct": None,
        "chunk-keys": None,
        "chunk-summary": None,
        "doc-keys": None,
        "doc-summary": None,
        "sect-instruct": None,
        "sect-summary": None,
    }


@pytest.mark.asyncio
async def test_async_methods_match_sync_source_loading_and_forwarding() -> None:
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

    definition = await client.load_extraction_definition_from_yaml(yaml_text=CUSTOM_WORKFLOW_YAML)
    direct_definition = await client.load_extraction_definition(yaml_text=CUSTOM_WORKFLOW_YAML)
    workflow_definition = await client.load_extraction_definition(
        workflow_id="workflow-1",
        yaml_text="not: [valid",
        request_options=request_options,
    )
    from_workflow = await client.load_extraction_definition_from_workflow(
        "workflow-1",
        request_options=request_options,
    )
    created = await client.create_extraction_workflow(
        definition=definition,
        yaml_text="not: [valid",
        name="statement extraction",
        request_options=request_options,
    )
    updated = await client.update_extraction_workflow(
        "workflow-1",
        definition=from_workflow,
        yaml_text="not: [valid",
        request_options=request_options,
    )

    assert created == "created"
    assert updated == "updated"
    assert workflows.calls[0] == ("get", "workflow-1", request_options)
    assert workflows.calls[1] == ("get", "workflow-1", request_options)
    assert workflows.calls[2][1]["request_options"] is request_options
    assert workflows.calls[3][2]["request_options"] is request_options
    assert workflows.calls[2][1]["template"]["{{LANGUAGE_UNKNOWN}}"] == ""
    assert direct_definition.extract == definition.extract
    assert workflow_definition.extract == from_workflow.extract
