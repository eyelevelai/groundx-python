import typing

from groundx.core.http_client import get_request_body
from groundx.types import (
    WorkflowDetail,
    WorkflowRequest,
    WorkflowStep,
    WorkflowStepConfig,
    WorkflowSteps,
)
from groundx.workflows.raw_client import RawWorkflowsClient


class _DummyWorkflowResponse:
    status_code = 200
    headers: typing.Dict[str, str] = {}
    text = ""

    def json(self) -> typing.Dict[str, typing.Any]:
        return {"workflow": {"workflowId": "9c79a6d3-65ac-4108-83cf-572cc7b6dbd8"}}


class _RecordingHttpClient:
    def __init__(self) -> None:
        self.calls: typing.List[typing.Tuple[str, typing.Dict[str, typing.Any]]] = []

    def request(self, path: str, **kwargs: typing.Any) -> _DummyWorkflowResponse:
        json_body, data_body = get_request_body(
            json=kwargs.get("json"),
            data=kwargs.get("data"),
            request_options=kwargs.get("request_options"),
            omit=kwargs.get("omit"),
        )
        encoded_kwargs = dict(kwargs)
        encoded_kwargs["json"] = json_body
        encoded_kwargs["data"] = data_body
        self.calls.append((path, encoded_kwargs))
        return _DummyWorkflowResponse()


class _RecordingWrapper:
    def __init__(self, http_client: _RecordingHttpClient) -> None:
        self.httpx_client = http_client


def _custom_workflow_parts() -> typing.Dict[str, typing.Any]:
    from groundx.types import (
        CustomWorkflowLeafField,
        CustomWorkflowOutputRoute,
        CustomWorkflowStep,
        CustomWorkflowStepConfig,
        CustomWorkflowStepElementConfig,
    )

    return {
        "template": {"BILLING_HINT": "Prefer values from the charge table."},
        "custom_steps": [
            CustomWorkflowStep(
                name="line_item_labels",
                level="chunk",
                kind="keys",
                required_template_keys=["BILLING_HINT"],
                config=CustomWorkflowStepConfig(
                    all_=CustomWorkflowStepElementConfig(
                        includes={"text": True},
                    )
                ),
            )
        ],
        "output_routes": [
            CustomWorkflowOutputRoute(
                workflow_group="line_items",
                workflow_field="description",
                final_path="/line_items/*/description",
                step_name="line_item_labels",
                level="chunk",
                output_map="customChunkOutputs",
                output_key="label",
                readback_path="/chunks/*/customChunkOutputs/line_item_labels/label",
            )
        ],
        "leaf_fields": [
            CustomWorkflowLeafField(
                final_path="/line_items/*/description",
                workflow_group="line_items",
                workflow_field="description",
                step_name="line_item_labels",
                level="chunk",
                output_key="label",
                field_type="str",
                is_repeated=True,
                repetition_scope="/line_items/*",
            )
        ],
    }


def _assert_custom_workflow_body(body: typing.Dict[str, typing.Any]) -> None:
    assert body["template"] == {
        "BILLING_HINT": "Prefer values from the charge table."
    }
    assert body["customSteps"][0]["name"] == "line_item_labels"
    assert body["customSteps"][0]["requiredTemplateKeys"] == ["BILLING_HINT"]
    assert body["customSteps"][0]["config"]["all"]["includes"] == {"text": True}
    assert body["outputRoutes"][0]["readbackPath"] == (
        "/chunks/*/customChunkOutputs/line_item_labels/label"
    )
    assert body["leafFields"][0]["repetitionScope"] == "/line_items/*"


def test_workflow_request_serializes_template_and_custom_steps() -> None:
    from groundx.types import (
        CustomWorkflowLeafField,
        CustomWorkflowOutputRoute,
        CustomWorkflowStep,
        CustomWorkflowStepConfig,
        CustomWorkflowStepElementConfig,
    )

    request = WorkflowRequest(
        name="line item workflow",
        template={
            "BILLING_HINT": "Prefer values from the charge table.",
        },
        steps=WorkflowSteps(
            chunk_keys=WorkflowStep(
                all_=WorkflowStepConfig(includes={"text": True}),
            )
        ),
        custom_steps=[
            CustomWorkflowStep(
                name="line_item_labels",
                level="chunk",
                kind="keys",
                required_template_keys=["BILLING_HINT"],
                config=CustomWorkflowStepConfig(
                    all_=CustomWorkflowStepElementConfig(
                        includes={"text": True},
                    )
                ),
            )
        ],
        output_routes=[
            CustomWorkflowOutputRoute(
                workflow_group="line_items",
                workflow_field="description",
                final_path="/line_items/*/description",
                step_name="line_item_labels",
                level="chunk",
                output_map="customChunkOutputs",
                output_key="label",
                readback_path="/chunks/*/customChunkOutputs/line_item_labels/label",
            )
        ],
        leaf_fields=[
            CustomWorkflowLeafField(
                final_path="/line_items/*/description",
                workflow_group="line_items",
                workflow_field="description",
                step_name="line_item_labels",
                level="chunk",
                output_key="label",
                field_type="str",
                is_repeated=True,
                repetition_scope="/line_items/*",
            )
        ],
    )

    payload = request.model_dump(by_alias=True, exclude_none=True)

    assert payload["template"]["BILLING_HINT"] == "Prefer values from the charge table."
    assert payload["steps"]["chunk-keys"]["all"]["includes"] == {"text": True}
    assert payload["customSteps"][0]["name"] == "line_item_labels"
    assert payload["customSteps"][0]["requiredTemplateKeys"] == [
        "BILLING_HINT"
    ]
    assert payload["customSteps"][0]["config"]["all"]["includes"] == {"text": True}
    assert "field" not in payload["customSteps"][0]["config"]["all"]
    assert payload["outputRoutes"][0]["readbackPath"] == (
        "/chunks/*/customChunkOutputs/line_item_labels/label"
    )
    assert payload["leafFields"][0]["repetitionScope"] == "/line_items/*"


def test_workflow_detail_deserializes_custom_routes_and_outputs() -> None:
    from groundx.types import (
        CustomWorkflowLeafField,
        CustomWorkflowOutputRoute,
        CustomWorkflowStep,
    )

    payload: typing.Dict[str, typing.Any] = {
        "workflowId": "9c79a6d3-65ac-4108-83cf-572cc7b6dbd8",
        "name": "line item workflow",
        "extract": {"line_items": {"fields": {}}},
        "template": {"BILLING_HINT": "Prefer values from the charge table."},
        "customSteps": [
            {
                "name": "line_item_labels",
                "level": "chunk",
                "kind": "keys",
                "requiredTemplateKeys": ["BILLING_HINT"],
            }
        ],
        "outputRoutes": [
            {
                "workflowGroup": "line_items",
                "workflowField": "description",
                "finalPath": "/line_items/*/description",
                "stepName": "line_item_labels",
                "level": "chunk",
                "outputMap": "customChunkOutputs",
                "outputKey": "label",
                "readbackPath": "/chunks/*/customChunkOutputs/line_item_labels/label",
            }
        ],
        "leafFields": [
            {
                "finalPath": "/line_items/*/description",
                "workflowGroup": "line_items",
                "workflowField": "description",
                "stepName": "line_item_labels",
                "level": "chunk",
                "outputKey": "label",
                "fieldType": "str",
                "isRepeated": True,
                "repetitionScope": "/line_items/*",
            }
        ],
        "steps": {
            "chunk-keys": {
                "all": {
                    "includes": {"text": True},
                }
            }
        },
    }

    detail = WorkflowDetail.model_validate(payload)

    assert detail.custom_steps is not None
    assert detail.output_routes is not None
    assert detail.leaf_fields is not None
    assert isinstance(detail.custom_steps[0], CustomWorkflowStep)
    assert isinstance(detail.output_routes[0], CustomWorkflowOutputRoute)
    assert isinstance(detail.leaf_fields[0], CustomWorkflowLeafField)
    assert detail.custom_steps[0].name == "line_item_labels"
    assert detail.output_routes[0].readback_path == (
        "/chunks/*/customChunkOutputs/line_item_labels/label"
    )
    assert detail.leaf_fields[0].repetition_scope == "/line_items/*"
    assert detail.steps is not None
    assert detail.steps.chunk_keys is not None


def test_workflow_create_and_update_calls_serialize_custom_config() -> None:
    http_client = _RecordingHttpClient()
    client = RawWorkflowsClient(
        client_wrapper=typing.cast(typing.Any, _RecordingWrapper(http_client))
    )
    parts = _custom_workflow_parts()

    client.create(
        name="line item workflow",
        extract={"line_items": {"fields": {}}},
        **parts,
    )
    client.update(
        "9c79a6d3-65ac-4108-83cf-572cc7b6dbd8",
        name="line item workflow",
        extract={"line_items": {"fields": {}}},
        **parts,
    )

    assert http_client.calls[0][0] == "v1/workflow"
    assert http_client.calls[0][1]["method"] == "POST"
    _assert_custom_workflow_body(http_client.calls[0][1]["json"])
    assert http_client.calls[1][0] == (
        "v1/workflow/9c79a6d3-65ac-4108-83cf-572cc7b6dbd8"
    )
    assert http_client.calls[1][1]["method"] == "PUT"
    _assert_custom_workflow_body(http_client.calls[1][1]["json"])
